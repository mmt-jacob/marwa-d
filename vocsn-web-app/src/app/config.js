import { sys_version, mod_version } from '../../package.json';

// Environment variables
const PRODUCTION = 'production';
const DEVELOPMENT = 'development';
export const SYS_VER = sys_version;
export const MOD_VER = mod_version;
let nodeEnv, gqlPort, gqlHost;
gqlHost = process.env.REACT_APP_HOST;
if (process.env.NODE_ENV === PRODUCTION) {
  nodeEnv        = PRODUCTION;
  gqlPort        = process.env.REACT_APP_GQL_PORT_PROD ;
} else {
  nodeEnv        = DEVELOPMENT;
  gqlPort        = process.env.REACT_APP_GQL_PORT_DEV ;
}
export const NODE_ENV = nodeEnv;
let client_gql_port = gqlHost + (NODE_ENV === PRODUCTION ? "" : (":" + gqlPort)) + "/graphql";
// let client_gql_port = gqlHost + ":" + gqlPort + "/graphql";
export const GQL_HOST = client_gql_port;

// Landing page
export const USE_VAL_LANDING = process.env.REACT_APP_USE_VAL_LANDING === "true";

// Session timeout parameters
export const INACTIVITY_MS_INTERVAL = 1000;
export const INACTIVITY_SHOWDIALOG =      parseInt(process.env.REACT_APP_INACTIVITY_SHOWDIALOG, 10);
export const INACTIVITY_LOGOUT =          parseInt(process.env.REACT_APP_INACTIVITY_LOGOUT, 10);

// Upload state timeouts
export const UPLOAD_TIMEOUT_PENDING =     parseInt(process.env.REACT_APP_TIMEOUT_PENDING , 10);
export const UPLOAD_TIMEOUT_UPLOADING =   parseInt(process.env.REACT_APP_TIMEOUT_UPLOADING , 10);
export const UPLOAD_TIMEOUT_QUEUED =      parseInt(process.env.REACT_APP_TIMEOUT_QUEUED , 10);
export const UPLOAD_TIMEOUT_PROCESSING =  parseInt(process.env.REACT_APP_TIMEOUT_PROCESSING , 10);
export const UPLOAD_TIMEOUT_RETRY_DELAY = parseInt(process.env.REACT_APP_RETRY_DELAY, 10);

// Unused in current configuration
export const AVATAR_IMAGE_PATH = "mike_offenbecher.jpg";
export const DEBUG = "Home";
export const DEBUG_AVATAR_IMAGE = "mike_offenbecher.jpg";
export const DEBUG_USER_FACILITIES = [{"facilityId":"100101","groups":[{"groupId":"0","roleId":3}]}];
export const DEBUG_USERNAME = "mike@techduke.io";
