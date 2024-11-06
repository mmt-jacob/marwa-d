/**
 * This file represents the User collection/table for the JSON memory database.
 */
import { randomBytes } from 'crypto';
import jsonData from '../json/User.json';
import { getUnixTimestamp } from '../../../utils';
import { DEFAULT_PASSWORD, DEFAULT_ROLEID, DEFAULT_USERNAME } from '../../ui_constants';

/**
 * Mock database collection/table for 'User'.
 */

const TAG = 'UserData:';

class User {
  constructor(obj) {
    // this.name = 'Room';
    if (obj) {
      // Clone passed object
      this.id = obj.id;
      this.timestamp = obj.timestamp;
      this.firstName = obj.firstName;
      this.lastName = obj.lastName;
      this.phone = obj.phone;
      this.imageFilename = obj.imageFilename;
      this.username = obj.username;
      this.password = obj.password;
      this.role = obj.role;
      this.facilityIds = obj.facilityIds;
    } else {
      // Create new, empty object
      this.id = undefined;
      this.timestamp = 0;
      this.firstName = '';
      this.lastName = '';
      this.phone = '';
      this.imageFilename = '';
      this.username = DEFAULT_USERNAME;
      this.password = DEFAULT_PASSWORD;
      this.role = DEFAULT_ROLEID;
      this.facilityIds = [];
    }
  }
}

/**
 * User collection/table (as array of User objects)
 */
console.log(TAG, 'Mocking "User" DB collection...');
// const DEFAULT_USER = new User();

// User collection/table - loaded from JSON file into an array only once.
// Step through JSON objects to create User objects mapped into an array.
const users = jsonData.map((obj) => {
  const user = new User(obj);
  user.id = randomBytes(10).toString('hex'); // Auto-generate mock 10-byte ID
  user.timestamp = getUnixTimestamp(); // Current timestamp (date/time)
  return user;
});

const getUsers = () => users;

const updateUser = (user) => {
  for (let i = 0; i < users.length; i += 1) {
    if (users[i].id === user.id) {
      users[i] = new User(user); // Update the found user with new User object
      console.log(TAG, 'Successfully updated DB with user ID:', user.id);
      return; // Successfully found and updated user
    }
  }
  console.error(TAG, 'updateUser cannot find user ID:', user.id, 'so update failed');
};

const insertUser = (user) => {
  const userCopy = new User(user);
  userCopy.id = randomBytes(10).toString('hex'); // Auto-generate mock 10-byte ID
  userCopy.timestamp = getUnixTimestamp(); // Current timestamp (date/time)
  users.push(userCopy); // Insert new User object
};


export {
  User,
  // DEFAULT_USER,
  getUsers,
  updateUser,
  insertUser,
};
