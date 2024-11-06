/**
 * This file represents the RoomConfig and RoomConfigHistory tables for the JSON memory database.
 */
import { randomBytes } from 'crypto';
import jsonData from '../json/RoomConfig.json';
import { getUnixTimestamp /* ,convertToUnixTimestamp */ } from '../../../utils';
import {
  DEFAULT_ROOMID,
  DEFAULT_VOLUME,
  DEFAULT_SILENCE,
  DEFAULT_LANGUAGE,
  DEFAULT_FREQUENCY,
  DEFAULT_PERIOD,
  DEFAULT_PATIENTID,
  DEFAULT_NICKNAME,
  DEFAULT_RISKLEVEL,
  DEFAULT_RISKFACTORS,
} from '../../ui_constants';

const TAG = 'RoomConfigData:';

/**
 * Room class - Either create new, initialized Room object or clone a given Room object.
 */
class Room {
  constructor(obj) {
    // this.name = 'Room';
    if (obj) {
      // Clone passed object
      this.id = obj.id;
      this.timestamp = obj.timestamp;
      this.facilityId = obj.facilityId;
      this.roomId = obj.roomId;
      this.volume = obj.volume;
      this.silence = obj.silence;
      this.language = obj.language;
      this.frequency = obj.frequency;
      this.period = obj.period;
      this.patientId = obj.patientId;
      this.nickname = obj.nickname;
      this.riskLevel = obj.riskLevel;
      this.riskFactors = obj.riskFactors.slice(); // Make shallow copy of array (of strings)
    } else {
      // Create new, empty (default) object
      this.id = undefined;
      this.timestamp = 0;
      this.facilityId = undefined;
      this.roomId = DEFAULT_ROOMID;
      this.volume = DEFAULT_VOLUME;
      this.silence = DEFAULT_SILENCE;
      this.language = DEFAULT_LANGUAGE;
      this.frequency = DEFAULT_FREQUENCY;
      this.period = DEFAULT_PERIOD;
      this.patientId = DEFAULT_PATIENTID;
      this.nickname = DEFAULT_NICKNAME;
      this.riskLevel = DEFAULT_RISKLEVEL;
      this.riskFactors = DEFAULT_RISKFACTORS;
    }
  }
}

/**
 * RoomConfig History collection/table (as array of Room objects)
 */
console.log(TAG, 'Mocking "RoomConfigHistory" DB collection...');
const roomsHistory = [];

/**
 * RoomConfig collection/table (as array of Room objects)
 */
console.log(TAG, 'Mocking "RoomConfig" DB collection...');

// RoomConfig collection/table - loaded from JSON file into an array only once.
// Step through JSON objects to create Room objects mapped into an array.
const rooms = jsonData.map((obj) => {
  const room = new Room(obj);
  room.id = randomBytes(10).toString('hex'); // Auto-generate mock 10-byte ID
  room.timestamp = getUnixTimestamp(); // Current timestamp (date/time)
  return room;
});

const getRooms = () => rooms;

const updateRoom = (room) => {
  for (let i = 0; i < rooms.length; i += 1) {
    if (rooms[i].roomId === room.roomId) {
      roomsHistory.push(rooms[i]); // Save previous version of Room object into history table (array)
      rooms[i] = new Room(room); // Update the found room with new Room object
      console.log(TAG, 'Successfully updated DB with roomId:', room.roomId);
      return; // Successfully found and updated room
    }
  }
  console.error(TAG, 'updateRoom cannot find roomId:', room.roomId, 'so update failed');
};

const insertRoom = (room) => {
  const roomCopy = new Room(room);
  roomCopy.id = randomBytes(10).toString('hex'); // Auto-generate mock 10-byte ID
  roomCopy.timestamp = getUnixTimestamp(); // Current timestamp (date/time)
  rooms.push(roomCopy); // Insert new Room object
};

export { Room, getRooms, updateRoom, insertRoom };
