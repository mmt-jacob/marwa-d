import dotenv from 'dotenv';
import { logger } from './logger';
import { sys_version, mod_version } from '../package.json';

// Load environment variables from shared .env file into process.env.
dotenv.config({path: '../.env'});
const { env } = process;

// Environment variables
const PRODUCTION = 'production';
const DEVELOPMENT = 'development';
export const SYS_VER = sys_version;
export const MOD_VER = mod_version;
let nodeEnv, gqlPort, gqlHost, appPort, appHost, whitelist, tableName, tableKey, logLevel;
let emailAddress, emailHost, emailPort, emailIsSecure, emailUser, emailPass;
appHost        = env.REACT_APP_HOST;
tableName      = env.TABLE_NAME;
tableKey       = env.TABLE_KEY;
emailAddress   = env.EMAIL_ADDRESS;
emailHost      = env.EMAIL_HOST;
emailPort      = env.EMAIL_PORT;
emailIsSecure  = env.EMAIL_IS_SECURE;
emailUser      = env.EMAIL_USER;
emailPass      = env.EMAIL_PASS;
if (env.NODE_ENV === PRODUCTION) {
  nodeEnv        = PRODUCTION;
  appPort        = env.REACT_APP_PORT_PROD;
  gqlPort        = env.REACT_APP_GQL_PORT_PROD;
  gqlHost        = appHost + ":" + gqlPort;
  logLevel       = "info";
} else {
  nodeEnv        = DEVELOPMENT;
  appPort        = env.REACT_APP_PORT_DEV;
  gqlPort        = env.REACT_APP_GQL_PORT_DEV;
  gqlHost        = appHost + ":" + gqlPort;
  logLevel       = "debug";
}
export const NODE_ENV        = nodeEnv;
export const GQL_PORT        = gqlPort;
export const GQL_HOST        = gqlHost;
export const TABLE_NAME      = tableName;
export const TABLE_KEY       = tableKey;
export const EMAIL_ADDRESS   = emailAddress;
export const EMAIL_HOST      = emailHost;
export const EMAIL_PORT      = emailPort;
export const EMAIL_IS_SECURE = emailIsSecure;
export const EMAIL_USER      = emailUser;
export const EMAIL_PASS      = emailPass;
export const LOG_LEVEL       = logLevel;
export const isProdEnv = () => (NODE_ENV === PRODUCTION);
whitelist = [appHost, appHost + ":" + appPort];
export const WHITELIST = whitelist;

// Logger
export const LOGGER_FOLDER = 'logs';
export const LOG_FILE = `${LOGGER_FOLDER}/server.log`;
export const LOG_FILE_EXCEPTIONS = `${LOGGER_FOLDER}/exceptions.log`;

// Session timeout
const ms_interval = 1000;
export const INACTIVITY_LOGOUT = parseInt(env.REACT_APP_INACTIVITY_LOGOUT, 10) * ms_interval;


export const showConfigs = () => {
  // TODO: PRODUCTION ENVIRONMENT - EVENTUALLY DELETE THESE LOG STATEMENTS!
  logger.debug('------------------------------------------------------');
  logger.debug('CONFIGURATION VALUES:');
  logger.debug('*** EVENTUALLY DELETE THESE LOG STATEMENTS IN PRODUCTION ENVIRONMENT! ***');
  logger.debug('SYSTEM_VER:', SYSTEM_VER);
  logger.debug('MODULE_VER:', MODULE_VER);
  logger.debug('NODE_ENV:', NODE_ENV);
  logger.debug('PORT:', GQL_PORT);
  logger.debug('TABLE_NAME:', TABLE_NAME);
  logger.debug('TABLE_KEY:', TABLE_KEY);
  logger.debug('LOG_LEVEL:', LOG_LEVEL);
  logger.debug('LOG_FILE:', LOG_FILE);
  logger.debug('LOG_FILE_EXCEPTIONS:', LOG_FILE_EXCEPTIONS);
  logger.debug('CORS WHITELIST =', WHITELIST);
  logger.debug('------------------------------------------------------');
};
