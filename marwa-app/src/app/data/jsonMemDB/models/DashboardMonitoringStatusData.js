let id = 0;
function createData(
  room,
  status,
  date,
  time,
  risk,
) {
  id += 1;
  return {
    id,
    room,
    status,
    date,
    time,
    risk,
  };
}

const data = [
  createData('401', 'Not In Use', '12/01/17', '18:02', ''),
  createData('402', 'Not In Use', '12/04/17', '16:52', ''),
  createData('403', 'Ready',      '12/10/17', '11:35', 'High'),
  createData('404', 'Not In Use', '12/09/17', '08:45', ''),
  createData('405', 'Monitoring', '12/10/17', '14:58', ''),
  createData('406', 'Not In Use', '12/08/17', '08:25', ''),
  createData('407', 'Monitoring', '12/10/17', '12:05', ''),
  createData('408', 'Not In Use', '12/10/17', '08:50', ''),
  createData('409', 'Not In Use', '12/09/17', '09:25', ''),
  createData('410', 'Not In Use', '12/10/17', '09:10', ''),
  createData('411', 'Not In Use', '12/08/17', '08:46', ''),
  createData('412', 'Monitoring', '12/10/17', '09:30', 'High'),
  createData('413', 'Monitoring', '12/10/17', '10:21', ''),
  createData('414', 'Not In Use', '12/06/17', '08:22', ''),
  createData('415', 'Monitoring', '12/10/17', '11:17', ''),
];

const getData = (facilityId) => data; // TODO: 3/28/2018 Use facilityId

// export { getData /* ,getRow */ };
export default getData;
