import { getPropStr, getPropObjFromJSON } from '../dbAzure';

const TAG = 'RoomConfig';

/**
 * Class representing an Azure Table Storage "RoomConfig" table entity.
 * @param e - An entity from Azure Table Storage results.
 */
class RoomConfig {
  constructor(e) {
    if (e) {
      const partitionKey = e.PartitionKey._;
      const rowKey = e.RowKey._;
      const timestamp = e.Timestamp._;

      this.id = `${partitionKey}_${rowKey}`;
      this.timestamp = timestamp;
      this.facilityId = e.FacilityID._;
      this.groupId = getPropStr(e, 'GroupID');
      this.roomId = e.RoomID._;
      this.language = e.Language._;
      this.silence = getPropStr(e, 'Silence');
      this.volume = getPropStr(e, 'Volume');
      this.period = getPropStr(e, 'Period');
      this.frequency = getPropStr(e, 'Frequency');
      this.airBedSensitivity = getPropStr(e, 'AirBedSensitivity');
      this.patientId = getPropStr(e, 'PatientID');
      this.patientNickname = getPropStr(e, 'PatientNickname');
      this.patientRiskLevel = getPropStr(e, 'PatientRiskLevel');
      this.patientRiskFactorIds = getPropObjFromJSON(e, 'PatientRiskFactorIDs', TAG); // Parse JSON string into integer Array
      this.editedBy = e.EditedBy._;
      // this.dirty = e.Dirty._;
      this.monitorType = getPropStr(e, 'MonitorType');
      this.monitorSerial = getPropStr(e, 'MonitorSerial');
      this.initialAlarm = getPropStr(e, 'InitialAlarm');
      this.cmsSound = getPropStr(e, 'CmsSound');
    }
  }
}

export default RoomConfig;
