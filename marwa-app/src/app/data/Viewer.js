import { AVATAR_IMAGE_PATH, DEBUG, DEBUG_AVATAR_IMAGE, DEBUG_USER_FACILITIES, DEBUG_USERNAME } from '../config';
import { DEFAULT_USER_FACILITIES, DEFAULT_USERNAME } from './ui_constants';

class Viewer {
  constructor(viewerModel) {
    let facilities;
    if (viewerModel) {
      // Viewer from passed User (JSON memory DB) object
      this.username = viewerModel.username;
      this.avatarSrc = (viewerModel.avatarImage) ? AVATAR_IMAGE_PATH + viewerModel.avatarImage : undefined;
      facilities = viewerModel.viewerFacilities;
      this.authenticated = true;
      // console.log(TAG, 'Viewer from DB User object');
    } else if (DEBUG) {
      // Debug (developer) viewer
      this.username = DEBUG_USERNAME;
      this.avatarSrc = DEBUG_AVATAR_IMAGE;
      facilities = DEBUG_USER_FACILITIES;
      this.authenticated = false;
      // console.log(TAG, 'DEBUG viewer');
    } else {
      // Default viewer
      this.username = DEFAULT_USERNAME;
      this.avatarSrc = undefined;
      facilities = DEFAULT_USER_FACILITIES;
      this.authenticated = false;
      // console.log(TAG, 'Default viewer');
    }

    this.facilitiesByGroup = this.packageFacilitiesByGroup(facilities);
    this.currentFacilityAndGroup = null;
  }

  /**
   * Repackage facilities by group (from Viewer DB model). This provides a convenient way of generating menu options for
   * choosing a facility/group, and for accessing the current list of risk factors for the current facility.
   */
  packageFacilitiesByGroup = (viewerFacilities) => {
    const options = [];
    // If we have a valid user (logged in) and the user has any facilities assigned
    const numFacilities = (this.username !== '' && viewerFacilities !== undefined) ? viewerFacilities.length : 0;

    // Generate the menu options for choosing a facility/group
    for (let i = 0; i < numFacilities; i += 1) {
      const fg = viewerFacilities[i];
      if (fg.viewerGroups === undefined)
        return {};
      for (let j = 0; j < fg.viewerGroups.length; j += 1) {
        const currGroup = fg.viewerGroups[j];
        const option = {
          indexId: i + j,
          facilityId: fg.facilityId,
          facilityName: fg.facilityName,
          facilityRiskFactorOptions: fg.facilityRiskFactorOptions,
          groupId: currGroup.groupId,
          groupName: currGroup.groupName,
          roleId: currGroup.roleId,
        };
        options.push(option);
      }
    }
    return options;
  };

  setCurrentFacilityAndGroup = (index) => {
    this.currentFacilityAndGroup = this.facilitiesByGroup[index];
    // console.log(`Viewer: currentFacilityAndGroup:${this.currentFacilityAndGroup}`);
    return this;
  }
}

export default Viewer;
