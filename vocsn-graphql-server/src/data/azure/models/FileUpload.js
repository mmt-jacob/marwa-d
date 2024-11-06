import { getPropStr, getPropObjFromJSON } from '../dbAzure';
import { TABLE_NAME, TABLE_KEY } from '../../../config';

import logger from 'winston';
const TAG = 'FileUpload';

/**
 * Class representing an Azure Table Storage "RoomConfig" table entity.
 * @param e - An entity from Azure Table Storage results.
 */
class FileUpload {
  constructor(reportID, status) {

    // // Variables
    // logger.info("0.1");
    // logger.info(typeof file);
    // logger.info(file);
    // logger.info("0.2");
    // const {fileBuffer, fileName, mimetype, encoding} = file;  // does this need an await somehow?
    //
    // logger.info(typeof fileBuffer);
    // logger.info(fileBuffer);
    // logger.info(fileName);
    //
    // // Catch errors
    // try {
    //   logger.info("1");
    //   // Determine path and create it if needed
    //   let share = "vocsn-data";
    //   let account = "guest";    // TODO: look this up by serail number
    //   let [year, month] = date.split('/');
    //   let directory = account + '/' + sn + '/' + year + '/' + month;
    //   logger.info("2");
    //   // Setup file stream
    //   let stream = require('stream');
    //   let azure = require('azure-storage');
    //   let fileService = azure.createFileService(TABLE_NAME, TABLE_KEY);
    //   let fileStream = new stream.Readable();
    //   fileStream.push(fileBuffer);
    //   logger.info("3");
    //   // Upload file
    //   // fileService.createFileFromStream(share, directory, fileName, fileStream, fileBuffer.length, function (error, result, response) {
    //   //   if (!error) {
    //   //     // file uploaded
    //   //   }
    //   // });
    //   logger.info("4");
    //   // Attach resulting fields
    //   this.fileName = "No file name available.";
    //   this.account = account;
    //   this.path = directory;
    //   this.success = true;
    //   this.error = null;
    //
    // } catch (err) {
    //   logger.warn(err);
    //   this.fileName = "No file name available.";
    //   this.account = "";
    //   this.path = "";
    //   this.success = false;
    //   this.error = err;
    // }

    this.reportID = reportID;
    this.status = status;

  }
}

export default FileUpload;
