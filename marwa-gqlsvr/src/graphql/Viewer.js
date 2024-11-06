import logger from 'winston';

/**
 * Class representing the model for the GraphQL schema "UserFacility" type (see schema.js).
 * This is used to help enforce conformance to GraphQL type definition.
 */
class ViewerFacility {
  constructor() {
    // this.name = 'ViewerFacility';
    this.facilityId = '';
    this.facilityName = '';
    this.viewerGroups = [];
  }
}

/**
 * Class representing the model for the GraphQL schema "UserGroupRole" type (see schema.js).
 * This is used to help enforce conformance to GraphQL type definition.
 */
class ViewerGroupRole {
  constructor() {
    // this.name = 'ViewerGroupRole';
    this.groupId = '';
    this.groupName = '';
    this.roleId = 0;
  }
}

// /**
//  * Class representing the model for the GraphQL schema "RiskFactor" type (see schema.js).
//  * This is used to help enforce conformance to GraphQL type definition.
//  */
// class RiskFactor {
//   constructor() {
//     this.id = 0;
//     this.name = '';
//   }
// }

/**
 * Class representing the model for the GraphQL schema "Viewer" type (see schema.js).
 * This is used to help enforce conformance to GraphQL type definition.
 */
class Viewer {
  constructor(userModel, facilityModels) {
    this.username = userModel.username;
    this.password = userModel.password;
    this.firstName = userModel.firstName;
    this.lastName = userModel.lastName;
    this.phone = userModel.phone;
    this.avatarImage = userModel.avatarImage;
    this.viewerFacilities = [];

    // TODO: 8/14/2018 Here is where we could implement 'superuser' access to all facilities

    // Get only those facilities assigned to this user
    for (let i = 0; i < userModel.facilityGroups.length; i += 1) {
      // Find facility with matching id
      const fg = userModel.facilityGroups[i];
      const fList = facilityModels.filter(x => x.facilityId === fg.facilityId);
      if (fList.length === 1) { // Found unique matching id
        const viewerFacility = this.buildViewerFacility(fg.groups, fList[0]);
        this.viewerFacilities.push(viewerFacility);
      }
    }
  }

  /**
   * Create object that resolves to 'ViewerFacility' GraphQL type definition (see schema.js)
   */
  buildViewerFacility = (userFacilityGroups, facilityModel) => {
    const viewerFacility = new ViewerFacility();
    viewerFacility.facilityId = facilityModel.facilityId;
    viewerFacility.facilityName = facilityModel.name;
    viewerFacility.facilityRiskFactorOptions = facilityModel.riskFactorOptions;

    // For each facility, populate list of groups with roles
    for (let j = 0; j < userFacilityGroups.length; j += 1) {
      const fg = userFacilityGroups[j];
      const gList = facilityModel.groups.filter(x => x.groupId === fg.groupId);
      if (gList.length === 1) {
        const groupModel = gList[0];

        // Create object that resolves to 'ViewerGroupRole' GraphQL type definition (see schema.js)
        const viewerGroup = new ViewerGroupRole();
        viewerGroup.groupId = groupModel.groupId;
        viewerGroup.groupName = groupModel.name;
        viewerGroup.roleId = fg.roleId;

        viewerFacility.viewerGroups.push(viewerGroup);
      } else {
        logger.warn(`Zero or multiple User FacilityGroup w/groupId:${fg.groupId} found for facilityId:${facilityModel.facilityId}`);
      }
    }
    return viewerFacility;
  };
}

export default Viewer;
// export { Viewer, ViewerFacility, ViewerGroupRole };
