/**
 * Set up Winston as our Logger.
 * Ref: https://www.npmjs.com/package/winston
 */
import winston from 'winston'; // Our chosen logger package
import fs from 'fs';
import { isProdEnv, LOG_LEVEL, LOGGER_FOLDER, LOG_FILE, LOG_FILE_EXCEPTIONS } from './config';

export const logger = winston;

export const initLogger = () => {

  // Automatically create log file directory required by Winston (if necessary)
  if (!fs.existsSync(LOGGER_FOLDER)) {
    fs.mkdirSync(LOGGER_FOLDER);
  }

  winston.level = LOG_LEVEL;
  winston.colorize = true; // NOTE: Doesn't appear to work in WebStorm

  // // Add separate exception logger to handle Uncaught Exceptions, and don't exit app after logging one
  // winston.exceptions.handle(new winston.transports.Console({
  //   json: false,
  //   timestamp: true,
  // }));

  // If production environment, log to files and don't exit upon uncaughtException:
  if (isProdEnv()) {
    // Log to file(s)
    winston.configure({transports: [
        new winston.transports.File({
          level: LOG_LEVEL,
          filename: LOG_FILE,
          timestamp: true,
          json: false,
          maxsize: 5242880, // 5MB
          maxFiles: 5,
        }),
        new winston.transports.Console({
          format: winston.format.simple(),
          json: false,
          timestamp: true,
        })
      ]});

    // Log exceptions to separate file(s)
    winston.exceptions.handle([
      new winston.transports.File({
        json: false,
        timestamp: true,
        filename: LOG_FILE_EXCEPTIONS,
    }),
      new winston.transports.Console({
        json: false,
        timestamp: true,
      })
    ]);

    // Disable exitOnError for production (otherwise app exits upon uncaughtException)
    // e.g. Failed to load resource: the server responded with a status of 404 (Not Found)
    winston.exitOnError = false; // Don't exit app after logging an uncaughtException (request blocks until timeout)
  } else {
    // Log to file(s)
    winston.configure({transports: [
        new winston.transports.Console({
          format: winston.format.simple(),
          json: false,
          timestamp: true,
        })
      ]});

    // Log exceptions to separate file(s)
    winston.exceptions.handle([
      new winston.transports.Console({
        json: false,
        timestamp: true,
      })
    ]);
    winston.exitOnError = true;
  }
};
