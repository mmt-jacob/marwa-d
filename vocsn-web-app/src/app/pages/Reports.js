import React, {createRef} from 'react';
import PropTypes from 'prop-types';
import { withStyles } from '@material-ui/core/styles';
import classNames from 'classnames';
import { Table, TableBody, TableCell, TableHead, TableRow } from '@material-ui/core';
import Typography from '@material-ui/core/Typography';
import CircularProgress from '@material-ui/core/CircularProgress';
import { Query } from 'react-apollo';
import logo from '../static/images/pdf.png';

import { GET_ROOMCONFIGS } from '../data/queries';
import {
  getPeriod, getRange, getProcessingStatus
} from '../data/ui_constants';
import { getDateStr, getTimeStr } from '../utils';

const styles = theme => ({
  content: {
    width: '100%',
    height: 'calc(70% - 30%)',
    margin: '0 auto',
    paddingTop: '25px',
    [theme.breakpoints.up('lg')]: {
      maxWidth: '940px',
    },
    [theme.breakpoints.up('xl')]: {
      maxWidth: '1140px',
    },
  },
  uploadPane: {
    position: 'absolute',
    top: '70px',
    left: '0px',
    right: '0px',
    height: '40%',
    backgroundImage: 'radial-gradient(100% 100% at center, #f2f2f3, #d7d8da)',
    zIndex: '-1',
    [theme.breakpoints.up('lg')]: {
      height: '200px',
    },
    [theme.breakpoints.up('xl')]: {
      height: '250px',
    },
  },
  centered: {
    height: '100%',
    width: '100%',
    display: 'table',
  },
  instructions: {
    color: '#8b8e94',
    fontStyle: 'italic',
    marginBottom: '3px',
  },
  hideMobile: {
    margin: '0px 20px',
    [theme.breakpoints.up('lg')]: {
      display: 'none',
    }
  },
  mobileHide: {
    marginTop: '30px',
    [theme.breakpoints.down('md')]: {
      display: 'none',
    }
  },
  aboveTable: {
    width: '100%',
    height: '50px',
    textAlign: 'center',
    paddingTop: '10px',
    marginTop: '20px',
    background: '#fff'
  },
  shadow: {
    boxShadow: '0px 2px 4px 2px #ccc',
    [theme.breakpoints.down('md')]: {
      display: 'none',
    }
  },
  table: {
    // Mimic Paper
    backgroundColor: theme.palette.common.white,
    // boxShadow: '0px 2px 4px 2px #ccc',
    boxShadow: 'none',
    // minWidth: 700,
    // //width: '50%',
  },
  tableHeader: {
    backgroundColor: theme.palette.primary.light,
  },
  tableHeadCell: {
    fontFamily: '"avenir-heavy","Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif',
    textAlign: 'center',
    verticalAlign: 'middle',
    fontSize: '18px',
    color: theme.palette.common.white,
    margin: 0,
    padding: theme.spacing(0.5),
  },
  tableCell: {
    textAlign: 'center',
    // verticalAlign: 'middle',
    margin: 0,
    padding: theme.spacing(0.5),
  },
  tableCellLeft: {
    textAlign: 'left',
    // verticalAlign: 'middle',
    margin: 0,
    padding: theme.spacing(0.5),
    paddingLeft: '10px',
  },
  button: {
    margin: 0,
    // margin: theme.spacing.unit,
  },
  buttonRoom: {
    margin: 0,
    padding: 0,
  },
  xButton: {
    padding: '24px 0px',
  },
  editCell: {
    paddingLeft: '0px',
  },
  chip: {
    margin: 2,
    fontSize: '12px',
    // margin: theme.spacing.unit,
  },
  progress: {
    margin: `0 ${theme.spacing(2)}px`,
  },
  muiButton: {
    fontFamily: '"avenir-heavy","Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif',
    fontSize: '16px',
    fontStyle: 'normal',
    margin: '0px 24px 12px 24px',
    borderRadius: '25px',
    color: 'white',
  },
  upload: {
    backgroundColor: theme.palette.secondary.light,

    // This is experimental
    '&:hover': {
      backgroundColor: theme.palette.primary.dark,
      // Reset on touch devices, it doesn't add specificity
      '@media (hover: none)': {
        // This toggles after clicks
        backgroundColor: theme.palette.secondary.dark,
      },
      //   '&$disabled': {
      //     backgroundColor: theme.palette.primary.light,
      //   },
      // },
      // '&$disabled': {
      //   color: theme.palette.secondary.light,
    },
  },
  noUploads: {
    textAlign: 'center',
    marginTop: '5px',
    paddingTop: '15px'
  },
  right: {
    float: 'right',
    marginLeft: '40px'
  },
  left: {
    float: 'left',
    marginLeft: '20px'
  }
});

const TAG = 'Reports';

class Reports extends React.Component {
  /**
   * Initialize Component's state using Property Initializer (then no need for constructor).
   * REF: In setState(), prevState is a reference to the previous state. It should not be directly mutated.
   * Instead, changes should be represented by building a new object based on the input from prevState and props.
   * Ref: https://reactjs.org/docs/react-component.html#setstate
   */

  state = {
    open: false,
    reports: [
      {
        reportID: 'R10235478',
        uploadDate: new Date('2019-08-10'),
        uploadFile: 'export_84698_10003658_20190810_120384.tar',
        reportStart: new Date('2019-08-03'),
        reportEnd: new Date('2019-08-09'),
        reportPeriod: 7,
        patientId: 1,
        status: 1
      },
      {
        reportID: 'R10235479',
        uploadDate: new Date('2019-08-20'),
        uploadFile: 'export_84698_10003658_20190819_132416.tar',
        reportStart: new Date('2019-08-12'),
        reportEnd: new Date('2019-08-12'),
        reportPeriod: 1,
        patientId: 1,
        status: 2
      },
      {
        reportID: 'R10235480',
        uploadDate: new Date('2019-08-28'),
        uploadFile: 'export_84698_10003658_20190828_121557.tar',
        reportStart: new Date('2019-07-30'),
        reportEnd: new Date('2019-08-28'),
        reportPeriod: 30,
        patientId: 1,
        status: 2
      },
      {
        reportID: 'R10235481',
        uploadDate: new Date('2019-09-01'),
        uploadFile: 'export_84698_10003658_20190829_141151.tar',
        reportStart: new Date('2019-08-03'),
        reportEnd: new Date('2019-08-29'),
        reportPeriod: 7,
        patientId: 1,
        status: 3
      },
      {
        reportID: 'R10235482',
        uploadDate: new Date('2019-09-08'),
        uploadFile: 'export_84698_10003658_20190905_120384.tar',
        reportStart: new Date('2019-08-29'),
        reportEnd: new Date('2019-09-04'),
        reportPeriod: 7,
        patientId: 1,
        status: 3
      },
      {
        reportID: 'R10235483',
        uploadDate: new Date('2019-09-15'),
        uploadFile: 'export_84698_10003658_20190915_120384.tar',
        reportStart: new Date('2019-09-03'),
        reportEnd: new Date('2019-09-09'),
        reportPeriod: 7,
        patientId: 1,
        status: 3
      }
    ],
  };

  handleDialogOpen = (upload) => {
    // const identifier = event.currentTarget.getAttribute('identifier'); // Get <Button> 'identifier' attribute
    // const [ groupId, roomId ] = identifier.split('_');
    // REF: const roomId = parseInt(identifierStr, 10); // Alternately as a Number, or undefined
    console.log('set upload');
    console.dir(upload);
    console.log(typeof upload);
    this.setState({
      open: true,
      test: upload.source,
      selected: {
        group: 'this is a test',
        room: 'room',
        reportOptions: upload
      },
    });
  };

  handleDelete = delItem => {
    let upList = [...this.state.uploads];
    for( let i = 0; i < upList.length; i++){
      const upload = upList[i];
      if (upload.source === delItem.source) {
        upList.splice(i, 1);
        break;
      }
    }
    this.setState({uploads: upList});
  };

  /**
   * Close dialog
   * IMPORTANT:
   *  Don't reset selected groupId and roomId, otherwise noticeable dialog widget changes display during dialog closing!
   *  i.e. selected: { groupId: DEFAULT_GROUPID, roomId: DEFAULT_ROOMID }
   */
  handleDialogClose = () => this.setState({ open: false });
  // TODO: Enhancement: Implement feedback w/Snackbar (https://material-ui-next.com/demos/snackbars/)?

  render() {
    // const { classes, theme, viewer: { facilityId, riskFactorOptions } } = this.props;
    const { classes, theme, viewer } = this.props;
    const { facilityId, groupId, facilityRiskFactorOptions } = viewer.currentFacilityAndGroup;
    const inputFile = createRef(null);
    const pad = 'dense'; // OR 'default', 'none', 'dense'
    let roomConfigs = null;

    // //////////////
    const date = new Date();
    const now = getDateStr(date);
    const time = getTimeStr(date);
    // const now = date.toDateString(); // Possible format: Sunday, 01/29/2018
    // const time = date.toLocaleTimeString();
    // //////////////

    return (
        <div className={classes.content}>
          <div className={classes.uploadPane} />
          <div className={classNames(classes.centered, classes.hideMobile)}>
            <div className={classes.instCont}>
              <Typography className={classes.instructions} variant='body1' color='inherit' paragraph>
                Upload not available on mobile devices
              </Typography>
            </div>
          </div>
          <div className={classes.shadow}>
            <div className={classes.aboveTable}>
              <Typography variant='headline' color='inherit'>
                Reports
              </Typography>
            </div>
            <Table className={classes.table}>
              <TableHead>
                <TableRow className={classes.tableHeader}>
                  <TableCell padding={pad} className={classes.tableHeadCell}>Upload Date</TableCell>
                  <TableCell padding={pad} className={classes.tableHeadCell}>Data File</TableCell>
                  <TableCell padding={pad} className={classes.tableHeadCell}>Period</TableCell>
                  <TableCell padding={pad} className={classes.tableHeadCell}>Date Range</TableCell>
                  <TableCell padding={pad} className={classes.tableHeadCell}>Report</TableCell>
                  <TableCell padding={pad} className={classes.tableHeadCell}>Status</TableCell>
                </TableRow>
              </TableHead>
              <Query query={GET_ROOMCONFIGS} variables={{ facilityId, groupId }}>
                {
                  ({ loading: loadingC, error: errorC, data: { roomConfigs } }) => {
                    console.log(TAG, 'Query: data.roomConfigs=', roomConfigs);
                    if (errorC) return `Error loading upload page: ${errorC.message}`;

                    if (loadingC) {
                      // If data not loaded yet, then show animated progress graphic
                      console.log(TAG, 'Query: loading data...');
                      return (
                          <TableBody>
                            <TableRow>
                              <td colSpan='5' className={classes.noUploads}>
                                <CircularProgress
                                    className={classes.progress}
                                    style={{ color: theme.palette.secondary.dark }}
                                    thickness={7}
                                />
                              </td>
                            </TableRow>
                          </TableBody>
                      );
                    }

                    if (this.state.reports.length === 0) {
                      // If no rooms found for this facility
                      return (
                          <TableBody>
                            <TableRow>
                              <td colSpan='5' className={classes.noUploads}>
                                <Typography variant='subheading' color='inherit' paragraph>
                                  {'No Files selected to upload.'}
                                </Typography>
                              </td>
                            </TableRow>
                          </TableBody>
                      );
                    }

                    console.log(TAG, 'Query: data loaded!');
                    return (
                      <React.Fragment>
                        <TableBody>
                          {this.state.reports.map(n => (
                            <TableRow key={n.reportID}>
                              <TableCell padding={pad} className={classes.tableCell}>DATE</TableCell>
                              <TableCell padding={pad} className={classes.tableCell}>{n.uploadFile}</TableCell>
                              <TableCell padding={pad} className={classes.tableCell}>{getPeriod(n.reportPeriod)}</TableCell>
                              <TableCell padding={pad} className={classes.tableCell}>{getRange(n.reportStart, n.reportEnd)}</TableCell>
                              <TableCell padding={pad} className={classes.tableCell}>
                                <img src={logo} className={classes.appLogo} alt='Report Dowload' />
                              </TableCell>
                              <TableCell padding={pad} className={classes.tableCell}>{getProcessingStatus(n.status)}</TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </React.Fragment>
                    );
                  }
                }
              </Query>
            </Table>
          </div>
          {/* Responsive Dialog that goes full-screen when on mobile-sized screens */}
          {/*<ReportOptionsDialog*/}
          {/*    reportOptions={this.state.selected.reportOptions}*/}
          {/*    open={this.state.open}*/}
          {/*    onClose={this.handleDialogClose}*/}
          {/*    editedBy={viewer.username}*/}
          {/*    // roomConfig={this.getSelectedRoomConfig(roomConfigs)}*/}
          {/*    riskFactorOptions={facilityRiskFactorOptions}*/}
          {/*/>*/}
        </div>
    );
  }
}

// NOTE: Use 'withStyles' when you want to provide styles through the Material-UI 'classes' object.
export default withStyles(styles, { withTheme: true })(Reports);
