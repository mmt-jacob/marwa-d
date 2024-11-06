import azure from 'azure-storage';
import logger from 'winston';
import { increment } from 'alphanum-increment';

import { TABLE_NAME, TABLE_KEY } from '../../config';

const crypto = require('crypto');

/**
 * Get the next available ID for a specified record type.
 * Uses Azure eTags and retries to ensure concurrency with other clients.
 */

const getNewID = async (logger, field) => {

  // Setup connection and variables
  const tableService = azure.createTableService(TABLE_NAME, TABLE_KEY);
  const entGen = azure.TableUtilities.entityGenerator;
  let captureError = null;
  let idResult = null;
  const retries = 10;

  // Retry in case concurrency check fails
  for (let i = 0; i < retries; i++) {
    try {
      let newID = await new Promise((resolve, reject) => {
        tableService.retrieveEntity("IDGenerators", field, "", function (error, result, response) {
          if (!error) {

            // Get results
            let prefix = result.Prefix._;
            let idNum = result.NextID._;
            let newID = (prefix + idNum).toUpperCase();

            // Prepare entity for reservation
            let nextID = increment(idNum, { dashes: false });
            result.NextID = entGen.String(nextID);
            idResult = result;
            resolve(newID);
          }
          else {
            reject(error);
          }
        });
      });

      // Reserve ID by incrementing nex ID in database.
      return await new Promise((resolve, reject) => {
        tableService.replaceEntity("IDGenerators", idResult, "", function (error, result, response) {

          // Successfully reserved ID
          if (!error) {
            resolve(newID);
          }

          // Reservation failed. try again if within retry policy.
          else {
            reject(error);
          }
        })
      })

    // Encountered error. Retry
    } catch (err) {
      captureError = err;
    }
  }
  throw captureError;
};



/**
 * Create a CSPRNG for use as a guest download key.
 */

const getGuestKey = async () => {
  return await new Promise((resolve, reject) => {
    crypto.randomBytes(256, (err, buf) => {
      if (err) {
        reject(err);
      } else {
        resolve(buf.toString('hex'));
      }
    })
  })
};


export { getNewID, getGuestKey };