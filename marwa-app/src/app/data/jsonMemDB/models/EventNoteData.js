/**
 * This file represents the EventNote and EventNoteHistory tables for the JSON memory database.
 */
import { randomBytes } from 'crypto';
import jsonData from '../json/EventNote.json';
import { getUnixTimestamp /* ,convertToUnixTimestamp */ } from '../../../utils';

const TAG = 'EventNoteData:';

/**
 * Note class - Either create new, initialized Note object or clone a given Note object.
 */
class Note {
  constructor(obj) {
    // this.name = 'Note';
    if (obj) {
      // Clone passed object
      this.id = obj.id;
      this.timestamp = obj.timestamp;
      this.eventId = obj.eventId;
      this.eventTimestamp = obj.eventTimestamp;
      this.eventLocation = obj.eventLocation;
      this.eventType = obj.eventType;
      this.eventNote = obj.eventNote;
    } else {
      // Create new, empty object
      this.id = undefined;
      this.timestamp = 0;
      this.eventId = undefined;
      this.eventTimestamp = 0;
      this.eventLocation = '';
      this.eventType = '';
      this.eventNote = '';
    }
  }
}

/**
 * Event Note History table (as 'notesHistory' array of Note objects)
 */
console.log(TAG, 'Mocking "EventNoteHistory" DB collection...');
const notesHistory = []; // TODO: Eventually assign its own new table id value, instead of re-using id from notes table


/**
 * EventNote table (as 'notes' array of Note objects)
 */
console.log(TAG, 'Mocking "EventNote" DB collection...');
const NO_NOTE = new Note();
let eventNoteId = 103652 - 1;

// Generate new table row identifier
function dbGetNextNoteId() {
  eventNoteId += 1;
  return eventNoteId;
}

// EventNote table - loaded from JSON file into an array only once.
// Step through JSON objects to create Note objects mapped into an array.
const notes = jsonData.map((obj) => {
  const note = new Note(obj);
  note.id = randomBytes(10).toString('hex'); // Auto-generate mock 10-byte ID
  note.timestamp = getUnixTimestamp(); // Current timestamp (date/time)
  note.eventId = dbGetNextNoteId();
  return note;
});

const getNotes = (facilityId) => notes; // TODO: 3/28/2018 Use facilityId

const updateNote = (note) => {
  for (let i = 0; i < notes.length; i += 1) {
    if (notes[i].eventId === note.eventId) {
      notesHistory.push(notes[i]); // Save previous version of note object into history table (array)
      notes[i] = new Note(note); // Update the found note with new note object
      console.log(TAG, 'Successfully updated DB with eventId:', note.eventId);
      return; // Successfully found and updated note
    }
  }
  console.error(TAG, 'updateNote cannot find eventId:', note.eventId, 'so update failed');
};

const insertNote = (note) => {
  const noteCopy = new Note(note);
  noteCopy.id = randomBytes(10).toString('hex'); // Auto-generate mock 10-byte ID
  noteCopy.timestamp = getUnixTimestamp(); // Current timestamp (date/time)
  notes.push(noteCopy); // Insert new Note object
};

export { Note, NO_NOTE, getNotes, updateNote, insertNote, dbGetNextNoteId };
