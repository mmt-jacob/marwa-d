import { getPropStr, getPropObjFromJSON } from '../dbAzure';

const TAG = 'Facility';

/**
 * Class representing an Azure Table Storage "Facility" table entity.
 * @param e - An entity from Azure Table Storage results.
 */
class Facility {
  constructor(e) {
    if (e) {
      const partitionKey = e.PartitionKey._;
      // const rowKey = e.RowKey._;

      // this.id = `${partitionKey}_${rowKey}`;
      this.id = `${partitionKey}`;
      this.timestamp = e.Timestamp._;
      if (e.hasOwnProperty('FacilityID')) {
        this.facilityId = e.FacilityID._;
      } else {
        this.facilityId = partitionKey;
      }
      this.name = e.Name._;
      this.shortName = e.ShortName._;
      this.address1 = e.Address1._;
      this.address2 = getPropStr(e, 'Address2');
      this.city = e.City._;
      this.state = e.State._;
      this.zip = e.Zip._;
      this.country = getPropStr(e, 'Country');
      this.contactName = getPropStr(e, 'ContactName');
      this.contactPhone = getPropStr(e, 'ContactPhone');
      this.contactEmail = getPropStr(e, 'ContactEmail');
      this.groups = getPropObjFromJSON(e, 'Groups', TAG);
      this.riskFactorOptions = getPropObjFromJSON(e, 'RiskFactorOptions', TAG);
    }
  }
}

export default Facility;
