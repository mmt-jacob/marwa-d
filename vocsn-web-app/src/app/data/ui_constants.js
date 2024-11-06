import green from '@material-ui/core/colors/green';
import red from '@material-ui/core/colors/red';
// import {getDateStr} from "../utils";

/**
 * Constants used in UI and those that are related to database values.
 */

export const DRAWER_WIDTH = 100;
export const DAY_MILLIES = 86400000;
export const HOUR_MILLIES = 3600000;
export const MINUTE_MILLIES = 60000;

// IDs representing all the pages to navigate to
export const NAV_HOME = 'HOME';
export const NAV_UPLOAD = 'UPLOAD';
export const NAV_REPORTS = 'REPORTS';
export const NAV_DASHBOARD = 'DASHBOARD';
export const NAV_GUEST_UPLOAD = 'GUEST UPLOAD';
export const NAV_ROOMCONFIG = 'Room Configuration';
export const NAV_EVENTNOTE = 'Event Note';
export const NAV_REMOTEDISPLAY = 'Remote Display';
export const NAV_SYSTEMCONFIG = 'System Configuration';
export const NAV_DEFAULT = NAV_HOME; // Note: This is the true default (home page)

const OFF = 'OFF'; // NOTE: Code must be a non-falsy, non-empty string for Material-UI <Select> 'value' attribute
const NONE = 'NONE'; // NOTE: Code must be a non-falsy, non-empty string for Material-UI <Select> 'value' attribute
export const validateCodeOFF = code => ((!code) ? OFF : code); // Validate falsy code values
export const validateCodeNONE = code => ((!code) ? NONE : code); // Validate falsy code values
// const code = (silenceCode === undefined || silenceCode === '') ? null : silenceCode; // Validate falsy code values

export const TZ_OFFSET = (dt) => { return new Date(dt).getTimezoneOffset() * 60000; };

// Lookup table to convert Room Configuration 'language' ISO 639-1 code to UI label
// TODO: 5/16/2018 Externalize these UI options into database (make data-driven) in new Localization table
export const OPTIONS_LANGUAGE = [
  { code: 'en', label: 'English' },
  { code: 'sp', label: 'Spanish' },
  { code: 'zh', label: 'Chinese' },
];

export const getPeriod = (days) => {
  if (days === 1) {
    return days.toString() + ' Day';
  } else {
    return days.toString() + ' Days';
  }
};

export const getDateStr = d => {
  return d.toLocaleDateString("en-US");
};

export const getDateTimeStr = (start, end) => {
  let endStr = (end.getMonth()+1) + "/" + end.getDate() + "/" + end.getFullYear() + " " +
      ("0" + end.getHours()).substr(-2) + ":" + ("0" + end.getMinutes()).substr(-2);
  if (endStr.slice(-5) === "00:00") {
    endStr = (end.getMonth()+1) + "/" + (end.getDate() - 1) + "/" + end.getFullYear() + " " +
        ("0" + (end.getHours() + 24)).substr(-2) + ":" + ("0" + end.getMinutes()).substr(-2);
  }
  return (start.getMonth()+1) + "/" + start.getDate() + "/" + start.getFullYear() + " " +
      ("0" + start.getHours()).substr(-2) + ":" + ("0" + start.getMinutes()).substr(-2) + " to " + endStr;
};

export const getStart = (end, period) => {
  let days = period.hours / 24;
  let daysMillis = days * DAY_MILLIES;
  return new Date(end.getTime() - daysMillis);
};

export const getRange = (start, end) => {
  // if (getDateStr(start) === getDateStr(end))
  //   return getDateStr(start);
  // if (end.getTime() - start.getTime() < DAY_MILLIES)
  //   return getDateTimeStr(start, end);
  // return getDateStr(start) + " to " + getDateStr(end);
  return getDateTimeStr(start, end);
};

export const roundDayDown = (dt) => {
  // let days = Math.floor(dt.getTime() / DAY_MILLIES);
  // let offset = dt.getTimezoneOffset();
  return new Date(dt.getFullYear(), dt.getMonth(), dt.getDate());
};

export const roundDayDownUTC = (dt) => {
  // let days = Math.floor(dt.getTime() / DAY_MILLIES);
  // let offset = dt.getTimezoneOffset();
  return new Date(Date.UTC(dt.getFullYear(), dt.getMonth(), dt.getDate()));
};

export const roundDayUp = (dt) => {
  let dayStart = roundDayDown(dt);
  return new Date(dayStart.getTime() + DAY_MILLIES);
};

export const tzCorrect = (dt) => {
  return new Date(dt.getTime() - TZ_OFFSET(dt));
};

export const tzReturn = (dt) => {
  return new Date(dt.getTime() + TZ_OFFSET(dt));
};

export const getHours = (dt) => {
  let offset = dt.getTimezoneOffset();
  let adjusted = dt.getTime() - offset * MINUTE_MILLIES;
  let hourMillies = adjusted % DAY_MILLIES;
  return Math.round(hourMillies / HOUR_MILLIES);
};

export const getHours24 = (dt) => {
  let hourIndex = dt.getHours() - 1;
  if (hourIndex === -1)
    hourIndex = 23;
  return hourIndex;
};

export const displayEndDate = (dt) => {
  if (dt === undefined)
    return new Date();
  let hourIndex = dt.getHours();
  if (hourIndex === 0)
    dt = new Date(dt.getTime() - DAY_MILLIES);
  return dt;
};

export const getLanguageLabel = (isoCode) => {
  const foundObj = OPTIONS_LANGUAGE.find(x => x.code === isoCode);
  return foundObj ? foundObj.label : `[${isoCode}]`; // If not found, then return invalid code string
};

// Lookup table to convert Room Configuration 'volume' code to UI label
export const OPTIONS_VOLUME = [
  { code: OFF, label: 'OFF' },
  { code: '1', label: '1' },
  { code: '2', label: '2' },
  { code: '3', label: '3' },
];
export const getVolumeLabel = (volumeCode) => {
  const code = validateCodeOFF(volumeCode);
  const foundObj = OPTIONS_VOLUME.find(x => x.code === code);
  return foundObj ? foundObj.label : `[${code}]`; // If not found, then return invalid code string
};

// File status
export const FileStatus = {
  RETRYING: -3,
  CANCELLED: -2,
  ERROR: -1,
  EDITING: 0,
  PENDING: 1,
  UPLOADING: 2,
  QUEUED: 3,
  PROCESSING: 4,
  COMPLETE: 5
};

// Error levels
export const ErrorLevel = {
  NO_ERRORS: 0,
  WARNINGS: 1,
  MINOR: 2,
  ADVISORY: 3,
  SECTION: 4,
  CRITICAL: 5
};

// Report period options
export const OPTIONS_PERIOD = [
  { code: 0, label: '1 Hour (no trend)', shortLabel: '1 Hour', hours: 1 },
  { code: 1, label: '3 Hours (no trend)', shortLabel: '3 Hours', hours: 3 },
  { code: 2, label: '6 Hours (no trend)', shortLabel: '6 Hours', hours: 6 },
  { code: 3, label: '12 Hours (no trend)', shortLabel: '12 Hours', hours: 12 },
  { code: 4, label: '1 Day (no trend)', shortLabel: '1 Day', hours: 24 },
  { code: 5, label: '3 Days (trend last 24 hours)', shortLabel: '3 Days', hours: 72 },
  { code: 6, label: '7 Days (trend last 24 hours)', shortLabel: '7 Days', hours: 168 },
  { code: 7, label: '30 Days (trend last week)', shortLabel: '30 Days', hours: 720 },
  { code: 8, label: '60 Days (trend last 2 weeks)', shortLabel: '60 Days', hours: 1440 },
  { code: 9, label: '90 Days (trend last 3 weeks)', shortLabel: '90 Days', hours: 2160 },
  // { code: 10, label: '6 Months (trend last month)', shortLabel: '6 Months', hours: 4320 },
];
export const getPeriodLabel = (periodCode) => {
  const code = validateCodeOFF(periodCode);
  const foundObj = OPTIONS_PERIOD.find(x => x.code === code);
  return foundObj ? foundObj.label : `[${code}]`; // If not found, then return invalid code string
};

// Report processing status
export const PROCESSING_STATUS = [
  { code: -3, label: 'Waiting to Retry' },
  { code: -2, label: 'Cancelled' },
  { code: -1, label: 'Error' },
  { code: 0, label: 'Editing' },
  { code: 1, label: 'Pending' },
  { code: 2, label: 'Uploading' },
  { code: 3, label: 'Queued' },
  { code: 4, label: 'Processing' },
  { code: 5, label: 'Complete' }
];

export const getProcessingStatus = (processingCode) => {
  const code = validateCodeOFF(processingCode);
  const foundObj = PROCESSING_STATUS.find(x => x.code === code);
  return foundObj ? foundObj.label : `[${code}]`; // If not found, then return invalid code string
};

// Lookup table to convert Room Configuration 'silence' code to UI label
export const OPTIONS_SILENCE = [
  { code: OFF, label: 'OFF' },
  { code: 'N', label: 'Night' },
  { code: 'D', label: 'Day' },
  { code: 'A', label: 'Always' },
];
export const getSilenceLabel = (silenceCode) => {
  const code = validateCodeOFF(silenceCode);
  const foundObj = OPTIONS_SILENCE.find(x => x.code === code);
  return foundObj ? foundObj.label : `[${code}]`; // If not found, then return invalid code string
};

// export const OPTIONS_PERIOD = [
//   { code: OFF, label: 'OFF' },
//   { code: '1', label: '1 minute' },
//   { code: '2', label: '2 minutes' },
//   { code: '3', label: '3 minutes' },
//   { code: '4', label: '4 minutes' },
//   { code: '5', label: '5 minutes' },
// ];
// export const getPeriodLabel = (periodCode) => {
//   const code = validateCodeOFF(periodCode);
//   const foundObj = OPTIONS_PERIOD.find(x => x.code === code);
//   return foundObj ? foundObj.label : `[${code}]`; // If not found, then return invalid code string
// };

export const OPTIONS_FREQUENCY = [
  { code: OFF, label: 'OFF' },
  { code: '1', label: '1 time' },
  { code: '2', label: '2 times' },
  { code: '3', label: '3 times' },
  { code: '4', label: '4 times' },
];
export const getFrequencyLabel = (freqCode) => {
  const code = validateCodeOFF(freqCode);
  const foundObj = OPTIONS_FREQUENCY.find(x => x.code === code);
  return foundObj ? foundObj.label : `[${code}]`; // If not found, then return invalid code string
};

export const OPTIONS_AIRBED = [
  { code: OFF, label: 'OFF' },
  { code: '1', label: '1 second' },
  { code: '2', label: '2 seconds' },
];
export const getAirBedLabel = (airBedCode) => {
  const code = validateCodeOFF(airBedCode);
  const foundObj = OPTIONS_AIRBED.find(x => x.code === code);
  return foundObj ? foundObj.label : `[${code}]`; // If not found, then return invalid code string
};

// Lookup table to convert Patient Risk Level 'patientRiskLevel' code to UI label
export const OPTIONS_RISKLEVEL = [
  { code: NONE, label: 'NONE' },
  { code: 'Low', label: 'Low' },
  { code: 'Med', label: 'Medium' },
  { code: 'High', label: 'High' },
];
export const getRiskLevel = (riskLevelCode) => {
  const code = validateCodeNONE(riskLevelCode);
  const foundObj = OPTIONS_RISKLEVEL.find(x => x.code === code);
  return foundObj ? foundObj.label : `[${code}]`; // If not found, then return invalid code string
};

/* TEST for getSilenceLabel
console.log('test1', getSilenceLabel(null));
console.log('test2', getSilenceLabel(undefined));
console.log('test3', getSilenceLabel(''));
console.log('test3', getSilenceLabel('A'));
console.log('test3', getSilenceLabel('N'));
console.log('test3', getSilenceLabel('D'));

Default value doesn't work for null, since null IS a value (is defined)
test1 null -- need to use my code, since default value doesn't work for null (only undefined)
test2 OFF
test3 OFF
test3 Always
test3 Night
test3 Day
 */


// User Authorization Roles
// IMPORTANT: Must match string (RowKey) values used in Azure Table Storage database table "UserRole".
// IMPORTANT: Must match values used in mockJsonMem database and corresponding constants defined in:
//   server/src/data/mockJsonMem/models/user.js
export const DB_USERROLE_GUEST = 0; // Note: Default user role (guests are not displayed as logged in)
export const DB_USERROLE_FACILITYUSER = 1;
export const DB_USERROLE_FACILITYADMIN = 2;
export const DB_USERROLE_MASTERADMIN = 3;

// Report sections
export const Sections = {
  TREND:       {code: 1, label: "Trend Summary", reportVal: 'trend_summary'},
  SETTINGS:    {code: 2, label: "Therapy Use and Settings Overview", reportVal: 'settings_summary'},
  ALARM:       {code: 3, label: "Alarm Summary", reportVal: 'alarm_summary'},
  MONITOR:     {code: 4, label: "Monitor Details", reportVal: 'monitor_details'},
  THERAPY_LOG: {code: 5, label: "Therapy Log", reportVal: 'therapy_log'},
  ALARM_LOG:   {code: 6, label: "Alarm Log", reportVal: 'alarm_log'},
  CONFIG_LOG:  {code: 7, label: "Configuration Log", reportVal: 'config_log'},
  EVENT_LOG:   {code: 8, label: "Event Log", reportVal: 'event_log'}
};

// Hours
export const HoursStart = [
  { code: 0, label: '00:00' },
  { code: 1, label: '01:00' },
  { code: 2, label: '02:00' },
  { code: 3, label: '03:00' },
  { code: 4, label: '04:00' },
  { code: 5, label: '05:00' },
  { code: 6, label: '06:00' },
  { code: 7, label: '07:00' },
  { code: 8, label: '08:00' },
  { code: 9, label: '09:00' },
  { code: 10, label: '10:00' },
  { code: 11, label: '11:00' },
  { code: 12, label: '12:00' },
  { code: 13, label: '13:00' },
  { code: 14, label: '14:00' },
  { code: 15, label: '15:00' },
  { code: 16, label: '16:00' },
  { code: 17, label: '17:00' },
  { code: 18, label: '18:00' },
  { code: 19, label: '19:00' },
  { code: 20, label: '20:00' },
  { code: 21, label: '21:00' },
  { code: 22, label: '22:00' },
  { code: 23, label: '23:00' },
];
export const HoursEnd = [
  { code: 1, label: '01:00' },
  { code: 2, label: '02:00' },
  { code: 3, label: '03:00' },
  { code: 4, label: '04:00' },
  { code: 5, label: '05:00' },
  { code: 6, label: '06:00' },
  { code: 7, label: '07:00' },
  { code: 8, label: '08:00' },
  { code: 9, label: '09:00' },
  { code: 10, label: '10:00' },
  { code: 11, label: '11:00' },
  { code: 12, label: '12:00' },
  { code: 13, label: '13:00' },
  { code: 14, label: '14:00' },
  { code: 15, label: '15:00' },
  { code: 16, label: '16:00' },
  { code: 17, label: '17:00' },
  { code: 18, label: '18:00' },
  { code: 19, label: '19:00' },
  { code: 20, label: '20:00' },
  { code: 21, label: '21:00' },
  { code: 22, label: '22:00' },
  { code: 23, label: '23:00' },
  { code: 24, label: '24:00' }
];


// Default Room Configuration values
// IMPORTANT: Must match values used in database (see RoomConfig table)!
export let DEFAULT_PERIOD = OPTIONS_PERIOD[6];
export let DEFAULT_END = roundDayUp(new Date(Date.now()));
export let DEFAULT_START = getStart(DEFAULT_END, DEFAULT_PERIOD);
export let DEFAULT_SECTIONS = [
  Sections.TREND,
  Sections.SETTINGS,
  Sections.ALARM,
  Sections.MONITOR,
];

export const DEFAULT_FACILITYID = '';
export const DEFAULT_GROUPID = '';
export const DEFAULT_ROOMID = '';
export const DEFAULT_VOLUME = OFF;
export const DEFAULT_SILENCE = OFF;
export const DEFAULT_LANGUAGE = OPTIONS_LANGUAGE[0].code;
export const DEFAULT_FREQUENCY = OFF;
// export const DEFAULT_PERIOD = OFF;
export const DEFAULT_AIRBED = OFF;
export const DEFAULT_PATIENTID = '0';
export const DEFAULT_NICKNAME = '';
export const DEFAULT_RISKLEVEL = NONE;
export const DEFAULT_RISKFACTORS = [];
export const DEFAULT_EDITEDBY = '';

// User default values
// IMPORTANT: Must match values used in database and corresponding constants defined in:
// TODO: 4/24/2018 server/src/data/mockJsonMem/models/user.js
export const DEFAULT_USERNAME = '';
export const DEFAULT_PASSWORD = '';
export const DEFAULT_ROLEID = DB_USERROLE_GUEST; // Note: This is the true default
export const DEFAULT_USER_FACILITIES = [];

// ==================UI THEME CONSTANTS==============
// Text colors for BigValue/GoalActual values compared to a goal
export const COLOR_BLACK = 'black'; // TODO: 6/7/2018 Is black color available from Material UI - doesn't appear so?
export const COLOR_GREEN = green;
// export const COLOR_YELLOW = yellow;
export const COLOR_RED = red;

// Material Design
// Our Theme: https://material.io/color/#!/?view.left=0&view.right=0&secondary.color=AED581&primary.color=4FC3F7
// Material-UI colors: https://material-ui-next.com/style/color/
// Override Material-UI's default palette values by defining a palette object for our theme:
export const themePalette = {
  palette: {
    primary: {
      // main: '#4fc3f7', // lightBlue[300]
      // light: '#8bf6ff',
      // dark: '#0093c4',
      main: '#2684C6',
      light: '#00B1E2',
      dark: '#014886',
      contrastText: '#fff', // e.g. color of AppBar child Button text to inherit, etc.
    },
    secondary: {
      // main: '#aed581', // lightGreen[300]
      // light: '#e1ffb1',
      // dark: '#7da453',
      main: '#55A852',
      light: '#95C951',
      dark: '#018648',
      contrastText: '#fff',
      // contrastText: '#000', // TODO: Does white work or is black '#000' better?
    },
    ternary: {
      main: '#f1aa1d',
      light: '#f6c96f',
      dark: '#d8940e',
      contrastText: '#fff',
    },
    disabled: {
      main: '#cacbce',
      light: '#efeff0',
      dark: '#a8a9ad',
      contrastText: '#fff',
    },
    error: {
      // main: '#f1301d80'
      main: 'rgb(241,48,29)',
    }
    // TODO: Override these default error palette colors? Orange instead?
    // Ref: https://material-ui-next.com/customization/theme-default/
    // error: {
    //   light: '#e57373',
    //   main: '#f44336',
    //   dark: '#d32f2f',
    //   contrastText: '#fff',
    // },
  },
  breakpoints: {
    values: {
      xs: 0,
      sm: 501,
      md: 775,
      lg: 1000,
      xl: 1200,
    },
  },
  typography: {
    fontFamily: '"avenir-roman","Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif',
    fontWeightMedium: 500,
    body1: {
      fontWeight: 500,
    },
    button: {
      fontStyle: 'italic',
    },
    subheading: {
      color: '#0088D7',
      fontSize: '16.5px',
    },
  },

  // TODO: Add optional custom theme styles: https://material-ui-next.com/customization/themes/#adding-custom-style
  // TODO: Example Usage: theme.status.danger
  // status: {
  //   danger: 'orange', // OR orange[500].
  // },

  // TODO: Optionally Customizing all instances of a component type by using 'overrides' key of the theme:
  // TODO: https://material-ui-next.com/customization/themes/#customizing-all-instances-of-a-component-type
  // overrides: {
  //   MuiButton: {
  //     // Name of the styleSheet
  //     root: {
  //       // Name of the rule
  //       background: 'linear-gradient(45deg, #FE6B8B 30%, #FF8E53 90%)',
  //       borderRadius: 3,
  //       border: 0,
  //       color: 'white',
  //       height: 48,
  //       padding: '0 30px',
  //       boxShadow: '0 3px 5px 2px rgba(255, 105, 135, .30)',
  //     },
  //   },
  // },
  overrides: {
    MuiChip: {
      root: {
        height: '26px',
      },
      label: {
        paddingLeft: '6px',
        paddingRight: '6px'
      }
    },
    MuiModal: {
      root: {
        zIndex: 1000,
      }
    },
    MuiMenuItem: {
      root: {
        '&$selected': {
          backgroundColor: 'white',
          "&& span": {
            color: 'black',
          }
        },
      },
    },
    MuiTableCell: {
      root: {
        '&:last-child': {
          paddingRight: '4px',
        },
        // '&:first-child': {
        //   padding: '0px 0px',
        // }
      }
    },
    // MuiListItemText: {
    //   root: {
    //     padding: '0px, 20px',
    //   },
    // },
  },
};
