const BASE10 = 10;

/**
 * Get number seconds since epoch - number representing the milliseconds elapsed between 1 January 1970 00:00:00 UTC.
 * NOTE: date.toISOString() may be used for string representation of UTC in ISO 8601 format, where the
 * timezone is always UTC, as denoted by the 'Z' suffix (e.g. "2018-03-05T20:31:20.914Z")
 * @param dateObj - Optional Date object. If none provided, then current date is used.
 * @returns {number}
 */
export function getUnixTimestamp(dateObj) {
  const date = (dateObj === undefined) ? new Date() : dateObj;
  const timestampUTC = date.getTime(); // UTC time representation of milliseconds since epoch (e.g. 1520350505527)
  console.debug(`timestampUTC: ${timestampUTC} (${date.toISOString()})`); // 1520350505527 ('2018-03-05T20:31:20.914Z')
  return Math.floor(timestampUTC / 1000); // Convert to UNIX timestamp in seconds, truncating fractional seconds
}

/**
 * Convert date and optional time strings to Unix timestamp.
 * @param date - date format: 'yyyy-MM-dd'
 * @param time - time format: 'hh:mm' (24-hr clock) - optional argument
 * @returns {number}
 */
export function convertToUnixTimestamp(date, time) {
  // Parse date format: 'yyyy-MM-dd'
  const year = parseInt(date.slice(0, 4), BASE10);
  const month = parseInt(date.slice(5, 7), BASE10) - 1; // (-1 for 0-based)
  const day = parseInt(date.slice(8, 10), BASE10);

  // Since time is optional, setup defaults
  let hours = 0;
  let minutes = 0;
  if (time) {
    // Parse time format: 'hh:mm' (24-hr clock)
    hours = parseInt(time.slice(0, 2), BASE10);
    minutes = parseInt(time.slice(3), BASE10);
  }

  const d = new Date(year, month, day, hours, minutes);
  const timestampUTC = d.getTime();
  return Math.floor(timestampUTC / 1000); // Convert to UNIX timestamp in seconds, truncating fractional seconds
}

// export function getDateFromUnixTimestamp(unixTimestamp) {
//   const d = new Date(unixTimestamp * 1000);
//   return getDateStr(d);
// }

/**
 * For given Unix timestamp, return string formatted as: 'yyyy-MM-dd'
 * Note: This format is required by Material-UI TextField type='date'
 * @param unixTimestamp
 * Returns undefined or date string of format: 'yyyy-MM-dd'
 */
export function getLocalDate(unixTimestamp) {
  if (unixTimestamp) {
    const dateObj = new Date(unixTimestamp * 1000);
    return getDateStr(dateObj); // Format must be: 'yyyy-mm-dd'
  } else {
    return undefined;
  }
}

/**
 * For given Unix timestamp, return string formatted as: 'hh:mm' (24-hour clock).
 * Note: Seconds are sliced off from ('hh:mm:ss').
 * Note: This format is required by Material-UI TextField type='time'
 * @param unixTimestamp
 * Returns undefined or time string of format: 'hh:mm' (24-hour clock)
 */
export function getLocalTime(unixTimestamp) {
  if (unixTimestamp) {
    const dateObj = new Date(unixTimestamp * 1000);
    return getTimeStr(dateObj);
    // return dateObj.toTimeString().slice(0, 5); // Format must be: 'hh:mm:ss' (24-hour clock)
  } else {
    return undefined;
  }

  // ////////////
  // Alternate approaches
  // const dateObj = new Date(unixTimestamp * 1000);
  // const hours = dateObj.getHours().toString().padStart(2, '0');
  // const mins = dateObj.getMinutes().toString().padStart(2, '0');
  // const secs = dateObj.getSeconds().toString().padStart(2, '0');
  // const time = `${hours}:${mins}:${secs}`; // Format must be 24-hour clock
  // const time = dateObj.toLocaleTimeString('en-US', { hour12: false });
  // ////////////
}

/**
 * For given Date object, return the local date string formatted as: yyyy-MM-dd
 * @param dateObj
 * @returns {string}
 */
export function getDateStr(dateObj) {
  const year = dateObj.getFullYear();
  const month = (dateObj.getMonth() + 1).toString().padStart(2, '0');
  const day = dateObj.getDate().toString().padStart(2, '0');
  return `${year}-${month}-${day}`;
}

/**
 * For given Date object, return the local time string formatted as: hh:mm:ss AM/PM
 * Example: 4:15:30 PM
 * @param dateObj
 * @returns {string}
 */
export function getTimeStr(dateObj) {
  return dateObj.toLocaleTimeString();
  // Alternate: return the local time string formatted as: hh:mm
  // return dateObj.toTimeString().slice(0, 5); // Format must be: 'hh:mm:ss' (24-hour clock)
}

/**
 * For a given UTC date/time string (e.g. from Azure Table Storage Timestamp),
 * return the local date and time formatted as: yyyy-MM-dd hh:mm:ss AM/PM
 * @param utcDateString (e.g. '2018-06-20T17:12:11.567Z')
 * @returns {string}
 */
export function getLocalDateTimeFromUTC(utcDateString) {
  const dateObj = new Date(utcDateString);
  return `${getDateStr(dateObj)} ${getTimeStr(dateObj)}`;
}

/**
 * Tagged Template Literal that lets you define the template literal as a format string, and then returns a final
 * formatted string (like Java/Python), where the index of the variable to substitute is included between braces.
 * This is useful for passing only the format string (e.g. `${0}${1}${0}!`) as an argument or property, so the called
 * function or Component can provide the values to be substituted.
 *
 * USAGE:
 *   const taggedTemplate1 = fmtstr`${0}${1}${0}!`;
 *   const taggedTemplate2 = fmtstr`${0}%`;
 *   const taggedTemplate3 = fmtstr`0:${0}`;
 *   const s1 = taggedTemplate1('Y', 'A'); // "YAY!"
 *   const s2 = taggedTemplate2(100); // "100%"
 *   const s3 = taggedTemplate3(45); // "0:45"
 *   console.log(s1);
 *   console.log(s2);
 *   console.log(s3);
 *
 * REFERENCE:
 *   Tagged Template Literals
 *   https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Template_literals
 */
export function fmtstr(strings, ...keys) {
  return (function (...values) {
    const dict = values[values.length - 1] || {};
    const result = [ strings[0] ];
    keys.forEach((key, i) => {
      const value = Number.isInteger(key) ? values[key] : dict[key];
      result.push(value, strings[i + 1]);
    });
    return result.join('');
  });
}

// /**
//  * Tagged Template Literal function that concatenates a given value with the preceding and following strings located
//  * in the template literal. This could be expanded to multiple values if desired.
//  *
//  * USAGE:
//  *   const value1 = 7;
//  *   const value2 = 32;
//  *   const output1 = myTag`${value1}%`;
//  *   const output2 = myTag`0:${value2}`;
//  *   console.log('Test value1: ', output1);
//  *   console.log('Test value2: ', output2);
//  *   console.log(s3);
//  *
//  * REFERENCE:
//  *   Tagged Template Literals
//  *   https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Template_literals
//  */
// const myTag = (strings, value) => {
//   // console.log('string length=', strings.length)
//
//   // NOTE: Any element in 'strings' array may be an empty ('') string, depending on how template literal is defined.
//   const prefix = strings[0];
//   const suffix = strings[1];
//
//   console.log('prefix=', prefix);
//   console.log('suffix=', suffix);
//   return prefix + value + suffix;
// };

// // NOTE: From JavaScript Mozilla developer's network
// function getRandomInt(min, max) {
//   const min2 = Math.ceil(min);
//   const max2 = Math.floor(max);
//   return Math.floor(Math.random() * (max2 - min2 + 1)) + min2;
// }
//
// function rand() {
//   return Math.floor(Math.random() * 20) - 10;
// }


/**
 * Generate multi-line string of given Object's properties.
 * @param obj - The Object to get properties from.
 * @param objName - Prefix string for each line.
 * @returns {string}
 */
export function getPropStrings(obj, objName) {
  let result = '';
  const keys = Object.keys(obj);
  for (let i = 0; i < keys.length; i += 1) {
    const name = keys[i];
    const value = obj[name];
    result += `${objName}.${name}: "${value}"\n`;
  }
  return result;
}
