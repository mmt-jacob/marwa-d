/**
 * This file represents the Facility collection/table for the JSON memory database.
 */
import { randomBytes } from 'crypto';
import jsonData from '../json/Facility.json';
import { getUnixTimestamp } from '../../../utils';

/**
 * Mock database collection/table for 'Facility'.
 *
 * NOTE: FacilityId is built as follows:
 * FacilityID = State + InstallType + StateFacilityNumber
 * (2 letter state ID, plus 2 letter installation type, plus 3 digits for up
 * to 1000 facilities of that type within a state)
 */

const TAG = 'FacilityData:';

class Facility {
  constructor(obj) {
    // this.name = 'Facility';
    if (obj) {
      // Clone passed object
      this.id = obj.id;
      this.timestamp = obj.timestamp;
      this.facilityId = obj.facilityId;
      this.name = obj.name;
      this.address1 = obj.address1;
      this.address2 = obj.address2;
      this.city = obj.city;
      this.state = obj.state;
      this.zip = obj.zip;
      this.phone = obj.phone;
      this.contactName = obj.contactName;
      this.createdBy = obj.createdBy;
    } else {
      // Create new, empty object
      this.id = undefined;
      this.timestamp = 0;
      this.facilityId = '';
      this.name = '';
      this.address1 = '';
      this.address2 = '';
      this.city = '';
      this.state = '';
      this.zip = '';
      this.phone = '';
      this.contactName = '';
      this.createdBy = '';
    }
  }
}

/**
 * Facility collection/table (as array of Facility objects)
 */
console.log(TAG, 'Mocking "Facility" DB collection...');

// Facility collection/table - loaded from JSON file into an array only once.
// Step through JSON objects to create Facility objects mapped into an array.
const facilities = jsonData.map((obj) => {
  const facility = new Facility(obj);
  facility.id = randomBytes(10).toString('hex'); // Auto-generate mock 10-byte ID
  facility.timestamp = getUnixTimestamp(); // Current timestamp (date/time)
  return facility;
});

const getFacilities = () => facilities;

const updateFacility = (facility) => {
  for (let i = 0; i < facilities.length; i += 1) {
    if (facilities[i].id === facility.id) {
      facilities[i] = new Facility(facility); // Update the found facility with new Facility object
      console.log(TAG, 'Successfully updated DB with facility ID:', facility.id);
      return; // Successfully found and updated facility
    }
  }
  console.error(TAG, 'updateFacility cannot find facility ID:', facility.id, 'so update failed');
};

const insertFacility = (facility) => {
  const facilityCopy = new Facility(facility);
  facilityCopy.id = randomBytes(10).toString('hex'); // Auto-generate mock 10-byte ID
  facilityCopy.timestamp = getUnixTimestamp(); // Current timestamp (date/time)
  facilities.push(facilityCopy); // Insert new Facility object
};


export {
  Facility,
  getFacilities,
  updateFacility,
  insertFacility,
};
