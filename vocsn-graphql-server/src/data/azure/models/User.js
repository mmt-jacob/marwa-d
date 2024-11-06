import { getPropStr, getPropObjFromJSON } from '../dbAzure';

const TAG = 'User';

// TODO: 8/10/2018 Possibly rename each 'azure' class to *Entity to distinguish between *Type GraphQL type definitions?

/**
 * Class representing an Azure Table Storage "User" table entity.
 * @param e - An entity from Azure Table Storage results.
 */
class User {
  constructor(e) {
    if (e) {
      const partitionKey = e.PartitionKey._;
      const rowKey = e.RowKey._;
      const timestamp = e.Timestamp._;

      this.id = `${partitionKey}_${rowKey}`;
      this.timestamp = timestamp;
      this.username = e.Username._;
      this.password = e.Password._;
      this.firstName = e.FirstName._;
      this.lastName = e.LastName._;
      this.phone = e.Phone._;
      this.avatarImage = getPropStr(e, 'AvatarImage');
      this.facilityGroups = getPropObjFromJSON(e, 'FacilityGroups', TAG);
    }
  }
}

export default User;
