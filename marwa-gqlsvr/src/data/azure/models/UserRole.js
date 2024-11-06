/**
 * Class representing an Azure Table Storage "UserRole" table entity.
 * @param e - An entity from Azure Table Storage results.
 */
class UserRole {
  constructor(e) {
    if (e) {
      const partitionKey = e.PartitionKey._;
      const rowKey = e.RowKey._;
      const timestamp = e.Timestamp._;

      this.id = `${partitionKey}_${rowKey}`;
      this.timestamp = timestamp;
      this.roleId = rowKey;
      this.roleName = e.Role._;
      this.description = e.Description._;
    }
  }
}

export default UserRole;
