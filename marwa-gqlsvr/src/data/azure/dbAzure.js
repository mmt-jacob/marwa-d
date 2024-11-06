import 'babel-polyfill';
import azure from 'azure-storage';
import logger from 'winston';

import { TABLE_NAME, TABLE_KEY, INACTIVITY_LOGOUT } from '../../config.js';
import FileUpload from './models/FileUpload.js';

const TAG = 'dbAzure';
const expireDays = 14;

import { getNewID, getGuestKey } from './id_generator.js';
import { sendSMTP } from "../../email.js";

/*
 ********** VOCSN Functions **********
 */


/**
 * Get client IP address from request header.
 * @param ctx - Request context
 * @returns {String}
 */

const getIP = (ctx) => {
  const req = ctx.req;
  return req.headers['x-real-ip'] ||
    req.headers['x-forwarded-for'] ||
    req.connection.remoteAddress ||
    req.socket.remoteAddress ||
    (req.connection.socket ? req.connection.socket.remoteAddress : null);
};


/**
 * Accepts an old session ID from a browser's local storage. This is checked against the
 * databse to verify the IP address and expiration date. If valid, the same session ID is
 * returned. Otherwise, a new session ID is returned.
 * @param ctx - Request context.
 * @param oldSessionID - Existing session ID.
 * @param accessKey - Access key associated with Session ID.
 * @returns {Promise<String>}
 */
class Session {
  constructor(sessionID, accessKey, expireDT) {
    this.sessionID = sessionID;
    this.accessKey = accessKey;
    this.expireDT = expireDT;
  }
}
const getSession = async (ctx, sessionID, accessKey) => {

  // Setup database connection
  const tableService = azure.createTableService(TABLE_NAME, TABLE_KEY);
  const entGen = azure.TableUtilities.entityGenerator;
  const sessionDuration = 12;  // Hours
  let table = "Sessions";

  // Lookup session
  const clientIP = getIP(ctx);
  let sessionResult = null;
  let authenticated;
  let entity = null;
  if ((sessionID !== "") && (accessKey !== "")) {
    entity = await new Promise((resolve, reject) => {
      tableService.retrieveEntity(table, clientIP, sessionID, async function (error, result, response) {

        // Got result
        if (!error && (result !== null)) {
          sessionResult = result;

          // Validate session
          let dbSessionID = result.RowKey._;
          let dbAccessKey = result.AccessKey._;
          let dbExpireDT = result.ExpireDT._;
          if ((accessKey === dbAccessKey) && (Math.floor(Date.now() / 1000) < dbExpireDT)) {
            resolve(result);
          } else {
            resolve(null);
          }
        } else {
          resolve(null);
        }
      })

      // Encountered error
    }).catch((error) => {
      logger.error("Failed to validate or generate session.");
      logger.error(error);
    });

    // Authenticated - keep credentials and update expiration time
    if (entity && (typeof entity === 'object')) {

      // Create session
      let dbSessionID = entity.RowKey._;
      let dbAccessKey = entity.AccessKey._;
      let now = new Date(new Date().toUTCString());
      let dbExpireDT = now.getTime() / 1000 + INACTIVITY_LOGOUT / 1000;
      entity.ExpireDT = entGen.Int32(dbExpireDT);
      authenticated = new Session(dbSessionID, dbAccessKey, dbExpireDT);
      if (authenticated && (typeof authenticated === 'object')) {
        let updated = await new Promise((resolve, reject) => {
          tableService.mergeEntity(table, entity, async function (error, result, response) {

            // Error
            if (error) {
              resolve(false);

              // Success
            } else {
              resolve(true);
            }
          })

          // Encountered error
        }).catch((error) => {
          logger.error("Failed to validate or generate session.");
          logger.error(error);
        });

        // Return updated session
        if (updated) {
          logger.info("Reload session: " + sessionID + " " + clientIP);
          return authenticated;

          // Unable to update session, continue and create new session
        } else {
          logger.info("Failed to update session");
        }
      }
    }
  }

  // Expired or invalid session - create new session/key pair
  sessionID = await getNewID(logger, "SessionID");
  accessKey = await getGuestKey();
  let now = new Date(new Date().toUTCString());
  let logonDT = now.getTime() / 1000 - 0.25 * 3600;
  let expireDT = now.getTime() / 1000 + INACTIVITY_LOGOUT / 1000;

  // Store session info in database
  const sessionEntity = {
    PartitionKey: entGen.String(clientIP),
    RowKey: entGen.String(sessionID),
    AccessKey: entGen.String(accessKey),
    LogonDT: entGen.Int32(logonDT),
    ExpireDT: entGen.Int32(expireDT),
  };

  // Create data file record
  table = "Sessions";
  return new Promise((resolve, reject) => {
    tableService.insertEntity(table, sessionEntity, function (error, result, response) {

      // Return new session/key pair
      if (!error) {
        logger.info("New session: " + sessionID + " " + clientIP);
        resolve(new Session(sessionID, accessKey, expireDT));

        // Unable to insert new session
      } else {
        logger.error(error);
        reject(error);
      }
    })
  })
};


/**
 * Checks a session/key/IP combination to validate session
 * @param ctx - Request context.
 * @param sessionID - Existing session ID.
 * @param accessKey - Access key associated with Session ID.
 * @returns {Promise<Boolean>}
 */

const validateSession = async (ctx, sessionID, accessKey) => {

  const tableService = azure.createTableService(TABLE_NAME, TABLE_KEY);

  // Lookup original session info
  const clientIP = getIP(ctx);
  let sessionEnt = await new Promise((resolve, reject) => {
    let table = "Sessions";
    tableService.retrieveEntity(table, clientIP, sessionID, function (error, result, response) {
      if (!error) {
        resolve(result);
      } else {
        reject(error);
      }
    })
  }).catch(error => {
    throw error;
  });

  // Validate session
  const now = Math.floor(new Date(new Date().toUTCString()) / 1000);
  if (!((sessionEnt.AccessKey._ === accessKey) &&
      (sessionEnt.PartitionKey._ === clientIP)) &&
      (now > sessionEnt.ExpireDT._)) {
    logger.warn("Warning: Unauthorized report request.");
    return false;
  }
  return true;
};

/**
 * Upload a single VOCSN data file.
 * @param ctx - Request context
 * @param sessionID - Session ID
 * @param upload - File stream buffer
 * @param sections - Selected sections for report
 * @param start - moment report starts
 * @param end - moment report ends
 * @param hours - Number of hours in report duration
 * @param size - buffer size
 * @param sn - unit serial number
 * @param exportDate - Date file was copied from VOCSN to USB
 * @param uploadDate - Time of upload in local time.
 * @param label - Report label
 * @returns {Promise<FileUpload>}
 */
const singleUpload = (ctx, sessionID, upload, sections, start, end, hours, size, sn, exportDate, uploadDate, label) =>
    (new Promise((resolve, reject) => {

  // Start saving file to file storage. Get file location back
  logger.info("Receiving file upload. " + sessionID + " " + sn + " " + exportDate);
  storeUpload(sessionID, upload, sections, start, end, hours, size, sn, label, exportDate, uploadDate)
      // Success - return new record IDs
      .then((fileUpload) => {
        resolve(fileUpload);
      })
      // Error - return error information
      .catch((err) => {
        logger.warn(`${TAG}.singleUpload: failureCallback ${err}`);
        reject(err);
      });
}));


// File status
export const FileStatus = {
  RETRYING: -3,
  CANCELLED: -2,
  ERROR: -1,
  PENDING: 0,
  EDITING: 1,
  UPLOADING: 2,
  QUEUED: 3,
  PROCESSING: 4,
  COMPLETE: 5
};


const storeUpload = async (sessionID, upload, sections, start, end, hours, size, sn, label,
                           exportDate, uploadDate) => {
  const { createReadStream, filename } = await upload;
  let status = FileStatus.ERROR;
  let share = "vocsn-data";
  let account = "guest";    // TODO: look this up by serial number
  start = new Date(start * 1000);
  end = new Date(end * 1000);
  exportDate = new Date(Math.floor(exportDate * 1000));
  uploadDate = new Date(uploadDate * 1000);
  let year = uploadDate.getFullYear().toString();
  let month = ("0" + (uploadDate.getMonth()+1).toString()).substr(-2);
  let day = ("0" + uploadDate.getDate().toString()).substr(-2);
  let directories = [year, month, day];

  // Variables for function results
  let uploadID = "";
  let dataFileID = "";
  let reportID = "";

  // Check path and create directories if needed
  let azure = require('azure-storage');
  let fileService = azure.createFileService(TABLE_NAME, TABLE_KEY);
  let directory = "";
  for (let x = 0; x < directories.length; x++) {
    if (directory != "/")
      directory += "/";
    directory += directories[x];
    await new Promise((resolve, reject) => {
      fileService.createDirectoryIfNotExists(share, directory, function (error, result, response) {
        if (!error) {
          resolve();
        }
         else {
           logger.error(error);
           reject(error);
         }
      });
    }).catch(error => { throw error; });
  }

  // Store the file in file storage.
  let dataStream = createReadStream();
  await new Promise((resolve, reject) => {
    fileService.createFileFromStream(share, directory, filename, dataStream, size, function (error, result, response) {
      if (!error) {
        logger.info("Successful upload: " & filename);
        status = FileStatus.QUEUED;
        resolve();
      }
      else {
        logger.error("Upload failed: " & filename);
        logger.error(error);
        dataStream.destroy();
        reject(error);
      }
    });
  }).catch(error => {
    dataStream.destroy();
    throw error;
  });

  // Create a data file record in the DataFile table
  dataFileID = await createDataFileEntity(sessionID, sn, exportDate, uploadDate, directory, filename);

  // Create an upload record in the Uploads table
  await createUploadEntity(sessionID, sn, exportDate, uploadDate, dataFileID);

  // Create a report record in the Reports table
  reportID = await createReportEntity(sessionID, sn, label, sections, dataFileID, hours, start, end, uploadDate,
      exportDate, status);

  // Create a report queue record in the ReportQueue table
  await createQueueEntity(sn, start, hours, uploadDate, reportID);

  // Return references and status information to client
  logger.info("Upload complete. " + sessionID + " " + sn + " " + uploadID);
  return new FileUpload(reportID, status);
};


const setStatus = async (ctx, sessionID, accessKey, snList, reportIdList, statusList) => {
  const tableService = azure.createTableService(TABLE_NAME, TABLE_KEY);
  const entGen = azure.TableUtilities.entityGenerator;

  // Lookup original session info
  let authorized = await validateSession(ctx, sessionID, accessKey);
  if (!authorized)
    return null;

  // Recall queue
  let table = "ReportQueue";
  let queue = await new Promise((resolve, reject) => {
    tableService.queryEntities(table, null, null, (error, result, response) => {
      if (!error) {
        resolve(result.entries);
      }
      else {
        logger.error(error);
        reject(error);
      }
    });
  }).catch(error => {
    logger.error(error.toString());
    throw error;
  });

  // Update each item
  for (let x=0; x<snList.length; x++) {
    let sn = snList[x];
    let reportID = reportIdList[x];
    let status = statusList[x];

    // Update report record
    table = "Reports";
    const updatedReportEntity = {
      PartitionKey: entGen.String(sn.toString()),
      RowKey: entGen.String(reportID),
      Status: entGen.Int32(status),
      ErrorLevel: entGen.Int32(5),
    };
    await new Promise((resolve, reject) => {
      tableService.mergeEntity(table, updatedReportEntity, function (error, result, response) {
        if (!error) {
          resolve();
        }
        else {
          logger.error(error);
          reject(error);
        }
      });
    }).catch(error => { logger.error(error); });

    // Update batch record
    for (let idx=0; idx < queue.length; idx++) {
      let batch = queue[idx];
      if (batch.ReportID._ === reportID) {

        // Delete record
        table = "ReportQueue";
        if ([FileStatus.ERROR, FileStatus.CANCELLED].includes(status)) {
          await new Promise((resolve, reject) => {
            tableService.deleteEntity(table, batch, function (error, result, response) {
              if (!error) {
                resolve();
              }
              else {
                logger.error(error);
                reject(error);
              }
            });
          }).catch(error => { logger.error(error); });

        // Update record
        } else {
          batch.Status = entGen.Int32(status);
          await new Promise((resolve, reject) => {
            tableService.mergeEntity(table, updatedReportEntity, function (error, result, response) {
              if (!error) {
                resolve();
              }
              else {
                logger.error(error);
                reject(error);
              }
            });
          }).catch(error => { logger.error(error); });
        }
      }
    }
  }
  return true;
};


const createDataFileEntity = async (sessionID, sn, exportDate, uploadDate, filePath, fileName) => {

  const tableService = azure.createTableService(TABLE_NAME, TABLE_KEY);
  const entGen = azure.TableUtilities.entityGenerator;
  let dataFileID = null;
  let test = null;
  try {
    // Prepare entity
    dataFileID = await getNewID(logger, "DataFileID");
    const dataFileEntity = {
      PartitionKey: entGen.String(sn.toString()),
      RowKey: entGen.String(dataFileID),
      ExportDT: entGen.Int32(exportDate.getTime() / 1000),
      UploadDT: entGen.Int32(uploadDate.getTime() / 1000),
      AccountID: entGen.String("Guest"),
      UserID: entGen.String("Guest"),
      SessionID: entGen.String(sessionID),
      FilePath: entGen.String(filePath),
      FileName: entGen.String(fileName),
    };

    // Create data file record
    await new Promise((resolve, reject) => {
      tableService.insertEntity("Datafiles", dataFileEntity, function (error, result, response) {
        if (!error) {
          resolve();
        }
        else {
          logger.error(error);
          reject(error);
        }
      });
    }).catch(error => { throw error; });

  // Handle errors
  } catch (error) {
    logger.error(error);
  }

  // Success
  return dataFileID;
};


const createUploadEntity = async (sessionID, sn, exportDate, uploadDate, dataFileID) => {

  const tableService = azure.createTableService(TABLE_NAME, TABLE_KEY);
  const entGen = azure.TableUtilities.entityGenerator;

  // Prepare entity
  const upload_entity = {
    PartitionKey: entGen.String(sn.toString()),
    RowKey: entGen.String(exportDate.toString()),
    SessionID: entGen.String(sessionID),
    UploadDT: entGen.Int32(uploadDate),
    DataFileID: entGen.String(dataFileID)
  };

  // Create upload record
  await new Promise((resolve, reject) => {
    tableService.insertEntity("Uploads", upload_entity, function (error, result, response) {
      if (!error || true) {     // TODO: Put this back once duplicate files are handles.
        resolve();
      }
       else {
         reject(error);
      }
    });
  // }).catch(error => { throw error; });    // TODO: Put this back once duplicate files are handles.
  })
};


const createReportEntity = async (sessionID, sn, label, sections, dataFileID, reportHours, reportStart, reportEnd,
                                  reportDate, exportDate, status) => {

  const tableService = azure.createTableService(TABLE_NAME, TABLE_KEY);
  const entGen = azure.TableUtilities.entityGenerator;

  // Prepare entity
  let queueDate = new Date(Date.now());
  let reportID = await getNewID(logger, "ReportID");
  const report_entity = {
    PartitionKey: entGen.String(sn.toString()),
    RowKey: entGen.String(reportID.toString()),
    AccountID: entGen.String("Guest"),
    DataFileID: entGen.String(dataFileID),
    LoginType: entGen.String("Guest"),
    ReportType: entGen.String("Usage"),
    ReportHours: entGen.Int32(reportHours),
    ReportStart: entGen.Int32(reportStart.getTime() / 1000),
    ReportEnd: entGen.Int32(reportEnd.getTime() / 1000),
    ReportDT: entGen.Int32(reportDate.getTime() / 1000),
    ExportDT: entGen.Int32(exportDate.getTime() / 1000),
    QueueDT: entGen.Int32(Math.round(queueDate.getTime() / 1000)),
    Sections: entGen.String(sections),
    FilePath: entGen.String(""),
    FileName: entGen.String(""),
    Label: entGen.String(label),
    Status: entGen.Int32(status),
    SessionID: entGen.String(sessionID),
    ErrorLevel: entGen.Int32(0)
  };

  // Create report record
  await new Promise((resolve, reject) => {
    tableService.insertEntity("Reports", report_entity, function (error, result, response) {
      if (!error) {
        resolve();
      }
      else {
        reject(error);
      }
    })
  }).catch(error => { throw error; });

  // Success
  return reportID;
};


const createQueueEntity = async (sn, startDate, hours, uploadDate, reportID) => {

  const tableService = azure.createTableService(TABLE_NAME, TABLE_KEY);
  const entGen = azure.TableUtilities.entityGenerator;

  // Prepare entity
  let queueID = await getNewID(logger, "QueueID");
  const queue_entity = {
    PartitionKey: entGen.String(sn.toString()),
    RowKey: entGen.String(queueID.toString()),
    UploadDT: entGen.String(Math.round(uploadDate.getTime() / 1000)),
    ReportID: entGen.String(reportID),
    Status: entGen.Int32(FileStatus.QUEUED),
    StartDT: entGen.Int32(Math.round(uploadDate.getTime() / 1000)),
    Hours: entGen.Int32(hours),
  };

  // Create report queue record
  await new Promise((resolve, reject) => {
    tableService.insertEntity("ReportQueue", queue_entity, function (error, result, response) {
      if (!error) {
        resolve();
      }
      else {
        reject(error);
      }
    })
  }).catch(error => { throw error; });
};


/**
 * Class representing the processing status of a report request.
  */
class ReportStatus {
  constructor(reportID, status, errorLevel) {
    this.reportID = reportID;
    this.status = status;
    this.errorLevel = errorLevel;
  }
}


/**
 * Upload a single VOCSN data file.
 * @param snList - File stream buffer
 * @param reportIdList - buffer size
 * @returns {Promise<[reportStatus]>}
 */

const getReportStatus = (snList, reportIdList) => {

  // Variables for function results
  let statusList = [];
  let pathList = [];
  let nameList = [];

  // Setup Azure connection
  let filter = "";
  const table = "Reports";
  const select = "RowKey, Status, FilePath, FileName";
  const tableService = azure.createTableService(TABLE_NAME, TABLE_KEY);

  // Construct a query
  for (let x = 0; x < snList.length; x++) {
    if (x > 0) {
      filter += " or ";
    }
    filter += "((PartitionKey eq '" + snList[x].toString() + "') and ";
    filter += "(RowKey eq '" + reportIdList[x].toString() + "'))";
  }
  let query = new azure.TableQuery().where(filter);
  if (filter === "")
    return null;

  return new Promise((resolve, reject) => {
    tableService.queryEntities(table, query, null, (error, result, response) => {
      if (!error) {
        const statusList = result.entries.map(ent => new ReportStatus(ent.RowKey._, ent.Status._, ent.ErrorLevel._));
        resolve(statusList);
      }
      else {
        logger.error(error);
        reject(error);
      }
    });
  }).catch(error => { reject(error); });
};

const getReportEnt = async (reportID, sn) => {

  const tableService = azure.createTableService(TABLE_NAME, TABLE_KEY);

  // Retrieve report record
  let table = "Reports";
  return await new Promise((resolve, reject) => {
    tableService.retrieveEntity(table, sn, reportID, null, (error, result) => {
      if (!error) {
        resolve(result);
      }
      else {
        logger.error(error);
        reject(error);
      }
    });
  });
};


const azureURI = async (fileService, share, path, file, sasToken) => {
  return new Promise(resolve => {
    setTimeout(() => {
      try {
        resolve(fileService.getUrl(share, path, file, sasToken, true));
      } catch (error) {
        logger.error("Error requesting URI from Azure.");
        resolve(null);
      }
    }, 200);
  })
};

const generateReportURI = async (reportEnt, fileName) => {

  return new Promise(async (resolve, reject) => {

    // Generate SAS policy
    const now = new Date(new Date().toUTCString());
    const start = new Date(now.getTime() - (0.25 * 3600000));
    const end = new Date(now.getTime() + (12 * 3600000));
    const sharedAccessPolicy = {
      AccessPolicy: {
        Permissions: azure.FileUtilities.SharedAccessPermissions.READ,
        Start: start,
        Expiry: end
      },
    };

    // Generate temporary URI
    const share = "vocsn-reports";
    const path = reportEnt.FilePath._;
    const file = reportEnt.FileName._;
    if ((fileName === null) || (fileName === undefined))
      fileName = file;
    const headers = {
      contentDisposition: 'attachment; filename="' + fileName + '"',
      cacheControl: "no-store, no-cache, must-revalidate",
      Pragma: "no-cache",
    };
    const fileService = azure.createFileService(TABLE_NAME, TABLE_KEY);
    const sasToken = fileService.generateSharedAccessSignature(share, path, file, sharedAccessPolicy, headers);

    // Try several times in case there is propagation lag in the server.
    let attempt = 0;
    let newUri = null;
    while (attempt < 3) {
      attempt++;
      try {
        newUri = await azureURI(fileService, share, path, file, sasToken);
        if ((newUri !== undefined) && (newUri !== null))
          attempt = 3;
      } catch (error) {
        logger.error(error);
        logger.error("Error: Unable to complete report URI request.");
        resolve(null);
      }
    }
    if ((newUri === undefined) || (newUri === null)) {
      logger.error("Unable to generate report URI");
      resolve(null);
    } else {
      resolve(newUri);
    }

  }).catch(error => {
    logger.error(error);
    return null;
  });
};


const delayedRetrieve = (table, sn, reportID) => {
  const tableService = azure.createTableService(TABLE_NAME, TABLE_KEY);

  console.log("GET REPORT", table, sn.toString(), reportID);

  return new Promise((resolve, reject) => {
    setTimeout(() => {

      tableService.retrieveEntity(table, sn.toString(), reportID, function (error, result) {
        if (!error) {
          resolve(result);
        } else {
          console.log("GET REPORT reject");
          reject(error);
        }
      });
    }, 150)

  }).catch(error => {
    logger.error(error);
  })
};


const getTempReportURI = async (ctx, getGuestKey, accessKey, sn, reportID) => {

  const tableService = azure.createTableService(TABLE_NAME, TABLE_KEY);
  const fileService = azure.createFileService(TABLE_NAME, TABLE_KEY);

  try {

    // Lookup report record
    let table = "Reports";
    let attempt = 0;
    let reportEnt;
    while (attempt < 3) {
      attempt++;
      reportEnt = await delayedRetrieve(table, sn, reportID);
      logger.info(reportEnt);
      logger.info(typeof reportEnt);
    }

    // Lookup original session info
    const clientIP = getIP(ctx);
    const sessionID = reportEnt.SessionID._;
    let sessionEnt = await new Promise((resolve, reject) => {
      let table = "Sessions";
      console.log("GET SESSION", table, clientIP, sessionID);
      tableService.retrieveEntity(table, clientIP, sessionID, function (error, result, response) {
        if (!error) {
          resolve(result);
        }
        else {
          reject(error);
        }
      })
    }).catch(error => { throw error; });

    // Validate session
    if (!((sessionEnt.AccessKey._ === accessKey) &&
      (sessionEnt.PartitionKey._ === clientIP))) {
      logger.warn("Warning: Unauthorized report request.");
      return null;
    }

    // Generate SAS and temporary URI
    return await generateReportURI(reportEnt);

  } catch (error) {
    logger.error(error);
    logger.error("Error: Unable to complete report request.");
    return null;
  }
};


class SessionReport {
  constructor(ent, uri) {
    this.reportID = ent.RowKey._;
    this.sn = ent.PartitionKey._;
    this.reportType = ent.ReportType._;
    this.reportHours = ent.ReportHours._;
    this.reportStart = ent.ReportStart._;
    this.reportEnd = ent.ReportEnd._;
    this.exportDate = ent.ExportDT._;
    this.sections = ent.Sections._;
    this.status = ent.Status._;
    this.label = (ent.Label !== undefined) ? ent.Label._ : "";
    this.uri = uri;
    this.errorLevel = ent.ErrorLevel._;
  }
}


/**
 * Recall reports listed in a session when the page is reloaded.
 * @param ctx - Context to get IP address.
 * @param sessionID - Session ID
 * @param accessKey - Access Key
 * @param snList - List of serisl numbers
 * @param reportIdList - List of reports last stored in the browser
 * @returns {Promise<[reportStatus]>}
 */

const getSessionReports = async (ctx, sessionID, accessKey, snList, reportIdList) => {

  const tableService = azure.createTableService(TABLE_NAME, TABLE_KEY);

  // Ignore empty requests
  if ((reportIdList === []) || (reportIdList.length !== snList.length))
    return null;

  try {

    // No reports to load
    if (reportIdList.length === 0)
      return null;

    // Lookup report record
    let reports = await new Promise((resolve, reject) => {
      let table = "Reports";
      let filter = "(";
      for (let x = 0; x < reportIdList.length; x++) {
        let reportID = reportIdList[x];
        let sn = snList[x];
        if (filter !== "(")
          filter += " or ";
        filter += "(PartitionKey eq '" + sn.toString() + "' and RowKey eq '" + reportID + "')";
      }
      filter += (") and (SessionID eq '" + sessionID + "')");
      const query = new azure.TableQuery().where(filter);
      tableService.queryEntities(table, query, null, function (error, result, response) {
        if (!error) {
          resolve(result.entries);
        }
        else {
          reject(error);
        }
      })
    }).catch(error => { throw error; });

    // If no reports found, return nothing
    if (reports.length === 0)
      return null;

    // Lookup original session info
    let authorized = await validateSession(ctx, sessionID, accessKey);
    if (!authorized)
      return null;

    // Generate new links and assemble result
    let result = [];
    for (let ent of reports) {
      let uri = "";
      if (ent.Status._ === FileStatus.COMPLETE)
        uri = await generateReportURI(ent);
      result.push(new SessionReport(ent, uri));
    }
    return result;

  } catch (error) {
    logger.error(error);
    logger.error("Error: Unable to complete session report request.");
    return null;
  }
};


/**
 * Request a batch download
 * @param ctx - Context to get IP address.
 * @param sessionID - Session ID
 * @param accessKey - Access Key
 * @param snList - List of serisl numbers
 * @param reportIdList - List of reports last stored in the browser
 * @param requestDT - Localized request time
 * @returns {Promise<[String]>}
 */
const makeBatchRequest = async (ctx, sessionID, accessKey, snList, reportIdList, requestDT) => {

  // Ignore empty requests
  if ((reportIdList === []) || (reportIdList.length !== snList.length))
    return null;

  try {

    // Lookup original session info
    console.log("BATCH CHECK !");
    let authorized = await validateSession(ctx, sessionID, accessKey);
    if (!authorized)
      return null;
    console.log("BATCH CHECK 2");
    // Create an upload record in the Batch table
    let batchID = await createBatchEntity(sessionID, snList, reportIdList, requestDT);
    console.log("BATCH CHECK 3");
    // Create an upload queue record in the BatchQueue table
    await makeBatchQueueRequest(batchID, sessionID, requestDT);
    console.log("BATCH CHECK 4");
    // Success
    return batchID;

  } catch (error) {
    logger.error(error);
    logger.error("Error: Unable to complete batch request.");
    return null;
  }
};

const createBatchEntity = async (sessionID, snList, reportIdList, requestDate) => {

  const tableService = azure.createTableService(TABLE_NAME, TABLE_KEY);
  const entGen = azure.TableUtilities.entityGenerator;
  console.log("BACTH ENT", "batches", TABLE_NAME, TABLE_KEY);
  // Prepare entity
  let batchID = await getNewID(logger, "BatchID");
  const batch_entity = {
    PartitionKey: entGen.String(sessionID.toString()),
    RowKey: entGen.String(batchID),
    AccountID: entGen.String("Guest"),
    LoginType: entGen.String("Guest"),
    RequestDT: entGen.Int32(requestDate),
    SNList: entGen.String(JSON.stringify(snList)),
    ReportIDList: entGen.String(JSON.stringify(reportIdList)),
    Status: entGen.Int32(FileStatus.QUEUED),
    Progress: entGen.Double(0.0),
    FileName: entGen.String(""),
    FilePath: entGen.String(""),
    Message: entGen.String("")
  };

  // Create report record
  await new Promise((resolve, reject) => {
    tableService.insertEntity("Batches", batch_entity, function (error) {
      if (!error) {
        resolve();
      } else {
        console.log("Batch Ent Reject");
        reject(error);
      }
    })
  }).catch(error => {
    console.log("Batch Ent Error");
    logger.error(error);
    throw error;
  });

  return batchID;
};

const makeBatchQueueRequest = async (batchID, sessionID, requestDT) => {

  const tableService = azure.createTableService(TABLE_NAME, TABLE_KEY);
  const entGen = azure.TableUtilities.entityGenerator;
  console.log("BACTH QUEUE ENT", "batches", TABLE_NAME, TABLE_KEY);
  // Prepare entity
  let now = new Date(Date.now());
  const batch_queue_entity = {
    PartitionKey: entGen.String(sessionID.toString()),
    RowKey: entGen.String(batchID),
    RequestDT: entGen.Int32(requestDT),
    StartDT: entGen.Int32(Math.round(now.getTime() / 1000)),
    Status: entGen.Int32(FileStatus.QUEUED),
  };

  // Create report record
  await new Promise((resolve, reject) => {
    tableService.insertEntity("BatchQueue", batch_queue_entity, function (error) {
      if (!error) {
        resolve();
      } else {
        console.log("Batch Queue Ent Reject");
        reject(error);
      }
    })
  }).catch(error => {
    console.log("Batch Queue Ent Error");
    throw error;
  });
};

const getBatchDownload = async (ctx, sessionID, accessKey, batchID) => {

  // Ignore empty requests
  if (batchID === [])
    return null;

  // Catch errors
  try {

    // Lookup original session info
    let authorized = await validateSession(ctx, sessionID, accessKey);
    if (!authorized)
      return null;

    // Get batch status
    let status = await getBatchStatus(batchID, sessionID);
    return status;

  // Handle errors
  } catch (error) {
    logger.error(error);
    logger.error("Error: Unable to complete batch status request.");
    return null;
  }

};

class BatchStatus {
  constructor(status, progress, URI, message) {
    this.status = status;
    this.progress = progress;
    this.URI = URI;
    this.message = message;
  }
}

const getBatchEnt = async (batchID, sessionID) => {

  const tableService = azure.createTableService(TABLE_NAME, TABLE_KEY);

  // Retrieve report record
  let table = "Batches";
  return await new Promise((resolve, reject) => {
    tableService.retrieveEntity(table, sessionID, batchID, null, (error, result) => {
      if (!error) {
        resolve(result);
      }
      else {
        logger.error(error);
        reject(error);
      }
    });
  });
};

const getBatchStatus = async (batchID, sessionID) => {

  const result = await getBatchEnt(batchID, sessionID);

  // Get values
  let status = parseInt(result.Status._);
  let progress = result.Progress._;
  let message = result.Message._;
  let URI = "";

  // Generate URI if file is ready
  if (status === FileStatus.COMPLETE) {
    URI = await getBatchURI(batchID, sessionID, result);
  }

  // Return batch status
  return new BatchStatus(
      status,
      progress,
      URI,
      message
  );
};

const getBatchURI = async (batchID, sessionID, batchEnt, filename=null) => {

  return new Promise(async (resolve, reject) => {

    // Generate SAS policy
    const now = new Date(new Date().toUTCString());
    const start = new Date(now.getTime() - (0.25 * 3600000));
    const end = new Date(now.getTime() + (expireDays * 24 * 3600000));

    const sharedAccessPolicy = {
      AccessPolicy: {
        Permissions: azure.FileUtilities.SharedAccessPermissions.READ,
        Start: start,
        Expiry: end
      },
    };
    // Generate default name
    const rDT = new Date(batchEnt.RequestDT._ * 1000);
    let M = "0" + (rDT.getUTCMonth() + 1);
    M = M.substr(M.length-2);
    let D = "0" + rDT.getUTCDate();
    D = D.substr(D.length-2);
    let h = "0" + rDT.getUTCHours();
    h = h.substr(h.length-2);
    let m = "0" + rDT.getUTCMinutes();
    m = m.substr(m.length-2);
    const date_str = rDT.getUTCFullYear() + "-" + M + "-" + D + " " + h + "-" + m;
    const defaultName = "VOCSN Multi-View Reports " +  date_str + ".zip";

    // Generate temporary URI
    const share = "vocsn-batches";
    const path = batchEnt.FilePath._;
    let file = batchEnt.FileName._;
    if (filename === null)
      filename = defaultName;
    const headers = {
      contentDisposition: "attachment; filename=" + filename,
      cacheControl: "no-store, no-cache, must-revalidate",
      Pragma: "no-cache",
    };
    const fileService = azure.createFileService(TABLE_NAME, TABLE_KEY);
    const sasToken = fileService.generateSharedAccessSignature(share, path, file, sharedAccessPolicy, headers);

    // Try several times in case there is propagation lag in the server.
    let attempt = 0;
    let newUri = null;
    while (attempt < 3) {
      attempt++;
      try {
        newUri = await azureURI(fileService, share, path, file, sasToken);
        if ((newUri !== undefined) && (newUri !== null))
          attempt = 5;
      } catch (error) {
        logger.error(error);
        logger.error("Error: Unable to complete batch URI request.");
        resolve(null);
      }
    }
    if ((newUri === undefined) || (newUri === null)) {
      logger.error("Unable to generate batch URI");
      resolve(null);
    } else {
      resolve(newUri);
    }

  }).catch(error => {
    logger.error(error);
    throw error;
  });
};

/**
 * Send email with download link
 * @param ctx - Request headers context
 * @param sessionID - Session ID
 * @param accessKey - Session access key
 * @param recordID - Record, either batch ID or report ID
 * @param fromName - Name of sender
 * @param subject - Email subject
 * @param toAddress - Recipient email address
 * @param link - Download link
 * @param fileName - Name of file to download
 * @param sendDate - Local date
 * @param multiple - Bool: more than one report included
 * @param sn - SN, required for reports only.
 * @return - <String>
 */

const sendEmail = async (ctx, sessionID, accessKey, recordID, fromName, subject, toAddress, link, fileName,
                         sendDate, multiple, sn) => {

  // Ignore empty requests
  if ((recordID === "" || recordID === null) ||
      (fromName === "" || fromName === null) ||
      (subject === "" || subject === null) ||
      (toAddress === "" || toAddress === null) || toAddress === [] ||
      (link === "" || link === null) ||
      (fileName === "" || fileName === null) ||
      (sendDate === "" || sendDate === null)) {
    logger.error("Received blank value in sendEmail.");
    return null;
  }

  // Catch errors
  try {

    // Lookup original session info
    let authorized = await validateSession(ctx, sessionID, accessKey);
    if (!authorized)
      return null;

    // Get expiration date
    const expireDate = new Date(Date.now() + (expireDays * 24 * 3600000));

    // Route to appropriate table
    const type = recordID.charAt(0);

    // Batch record
    if (type === "B") {
      const result = await getBatchEnt(recordID, sessionID);
      link = await getBatchURI(recordID, sessionID, result, fileName);
    }

    // Report record
    else if (type === "R") {
      if (sn === "" || sn === null)
          logger.error("SN required to email report.");
      const result = await getReportEnt(recordID, sn);
      link = await generateReportURI(result, fileName);
    }

    // Unsupported request
    else {
      logger.error("Unsupported email record request.");
      return null;
    }

    // Send email
    let messageIds = [];
    for (let address of toAddress) {
      messageIds.push(await sendSMTP(fromName, subject, address, link, fileName, sendDate, expireDate, multiple));
    }
    if (messageIds !== [])
      return messageIds;
    return null;

  // Handle errors
  } catch (error) {
    logger.error(error);
    logger.error("Error", error.stack);
    logger.error("Error", error.name);
    logger.error("Error", error.message);
    logger.error("Encountered error while sending email.");
    return null;
  }

};

export {
  singleUpload, getSessionReports, setStatus,
  getSession, getReportStatus, getTempReportURI,
  makeBatchRequest, getBatchDownload, sendEmail
};
