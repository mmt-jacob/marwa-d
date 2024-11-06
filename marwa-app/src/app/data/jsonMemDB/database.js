/**
 * Mock read-only JSON database.
 */
import { getUsers, updateUser, insertUser } from './models/UserData';
import { getFacilities, updateFacility, insertFacility } from './models/FacilityData';
import { getRooms, insertRoom, updateRoom } from './models/RoomConfigData';
import { getRiskFactors } from './models/RiskFactorsData';
import { getNotes, insertNote, updateNote } from './models/EventNoteData';

const TAG = 'database:';

// Mock the data
console.log(TAG, 'Mocking database...');

// Mock authenticated ID
// NOTE: graphql-relay's globalIdField() will generate the actual ID based on this value (it won't be this value)
const MOCK_AUTHENTICATED_ID = 3; // TODO: 3/26/2018 Eliminate this default user ID

/**
 * Create resolver functions used to resolve from GraphQL to Relay.
 */
// User collection (table)
const dbGetAllUsers = () => getUsers();
const dbGetUser = (username, password) => getUsers().find(x => x.username === username && x.password === password);
const dbGetUserById = id => getUsers().find(x => x.id === id);
const dbGetViewer = () => dbGetUserById(MOCK_AUTHENTICATED_ID);
const dbInsertUserDB = user => insertUser(user);
const dbUpdateUserDB = user => updateUser(user);

// Facility collection (table)
const dbGetFacilities = () => getFacilities();
const dbGetFacility = facilityId => getFacilities().find(x => x.facilityId === facilityId);
const dbInsertFacility = facility => insertFacility(facility);
const dbUpdateFacility = facility => updateFacility(facility);

// RoomConfig collection (table)
const dbGetRoomConfigs = facilityId => getRooms().filter(x => x.facilityId === facilityId);
// TODO: 2018/03/22 Test this:
const dbGetRoomConfig = (facilityId, roomId) => (
  getRooms().find(x => x.facilityId === facilityId && x.roomId === roomId)
);
const dbGetRoomIds = facilityId => getRooms().filter(x => x.facilityId === facilityId).map(config => config.roomId);
const dbInsertRoomConfig = room => insertRoom(room);
const dbUpdateRoomConfig = room => updateRoom(room);

// RiskFactors collection (table)
const dbGetFacilityRiskFactors = facilityId => getRiskFactors(facilityId);

// EventNote collection (table)
const dbGetEventNotes = (facilityId) => getNotes(facilityId);
const dbGetEventNote = id => getNotes().find(x => x.id === id);
const dbInsertEventNote = note => insertNote(note);
const dbUpdateEventNote = note => updateNote(note);

export {
  dbGetUser, dbGetUserById, dbGetViewer, dbGetAllUsers, dbInsertUserDB, dbUpdateUserDB,
  dbGetFacilities, dbGetFacility, dbInsertFacility, dbUpdateFacility,
  dbGetRoomConfig, dbGetRoomConfigs, dbInsertRoomConfig, dbUpdateRoomConfig, dbGetRoomIds,
  dbGetFacilityRiskFactors,
  dbGetEventNote, dbGetEventNotes, dbInsertEventNote, dbUpdateEventNote,
};

