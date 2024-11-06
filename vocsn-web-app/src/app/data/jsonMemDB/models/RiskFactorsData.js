/**
 * This file represents the RiskFactors table for the JSON memory database.
 */
import jsonData from '../json/RiskFactors.json';

const TAG = 'RiskFactorData:';

/**
 * RiskFactor class
 */
class RiskFactor {
  constructor(obj) {
    // this.name = 'RiskFactor';
    if (obj) {
      this.id = obj.id;
      this.facilityId = obj.facilityId;
      this.value = obj.value;
      this.label = obj.label;
    }
  }
}

console.log(TAG, 'Mocking "RiskFactor" DB collection...');

// RiskFactor table - List of possible risk factors (values), along with their UI labels, for all facilities.
// Step through objects from JSON file to create objects mapped into an array.
const riskFactors = jsonData.map(obj => new RiskFactor(obj));

const getRiskFactors = facilityId => riskFactors.filter(f => f.facilityId === facilityId);

export { getRiskFactors, RiskFactor };
