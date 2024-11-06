import azure from 'azure-storage';
import { TABLE_NAME, TABLE_KEY } from '../../config';
import schema from "../../graphql/schema";

/*
---------- Azure Database Initialization ----------
These functions check required tables in the database and automatically populate any that are missing. Not that with
Azure table storage, records are stored as files and do not follow a data type scheme. Therefore no fields need to be
mapped once the table is created. Each record written in the future will inherently contain a PartitionKey, RowKey, and
Timestamp. All other fields are optional and can be unique to each record.
 */

const init_tables = (logger) => {

  // Setup database access
  const tableService = azure.createTableService(TABLE_NAME, TABLE_KEY);
  const entGen = azure.TableUtilities.entityGenerator;

  // List of required tables
  const tables = [
    "Accounts",
    "Users",
    "Uploads",
    "DataFiles",
    "Reports",
    "ReportLog",
    "ReportQueue",
    "Batches",
    "BatchLog",
    "BatchQueue",
    "Sessions",
    "IDGenerators"
  ];

  // List of ID generator fields
  const generators = [
    ["AccountID", "A"],
    ["BatchID", "B"],
    ["DataFileID", "D"],
    ["ReportID", "R"],
    ["UploadID", "U"],
    ["QueueID", "Q"],
    ["SessionID", "S"]
  ];

  // Initialize tables
  let success = true;
  for (const table of tables) {
    try {
      tableService.createTableIfNotExists(table, function(error, result, response) {
        if (!error) {
          // Table exists or was created
        } else {
          // Table already exists
        }
      });
    }
    catch(error) {
      logger.error("Failed to verify/create table " + table);
      // Table existence check/creation failed
      // TODO: Handle errors
      success = false;
    }
  }

  // Initialize ID generator values
  for (const gen_def of generators) {
    const gen_name = gen_def[0];
    const gen_pre = gen_def[1];
    try {
      const gen_entity = {
        PartitionKey: entGen.String(gen_name),
        RowKey: entGen.String(""),
        Prefix: entGen.String(gen_pre),
        NextID: entGen.String("000000000")
      };
      tableService.insertEntity("IDGenerators", gen_entity, function (error, result, response) {
        if (!error || error.message === "The specified entity already exists.") {
          // Created record or it already exists
        } else {
          // Failed to check or create record
          success = false;
        }
      });
    }
    catch (error) {
      // Record existence check/creation failed
      logger.error("Failed to verify/create " + gen_name + " generator record.");
      success = false;
    }
  }

  return success;
};


const init_file_shares = (logger) => {

  // Setup file storage access
  const fileService = azure.createFileService(TABLE_NAME, TABLE_KEY);

  // List of required tables
  const shares = [
    "vocsn-data",
    "vocsn-reports",
    "vocsn-batches"
  ];

  // Process each share
  let success = true;
  for (const share of shares) {

    // Catch errors
    try {
      fileService.createShareIfNotExists(share, function(error, result, response) {
        if (!error) {
          // Created table
        } else {
          // Table already exists
        }
      });
    }
    catch(error) {
      logger.error(error);
      logger.error("Failed to verify/create file share  " + share);
      // Share existence check/creation failed
      // TODO: Handle errors
      success = false;
    }
  }
  return success;
};

export { init_tables, init_file_shares };
