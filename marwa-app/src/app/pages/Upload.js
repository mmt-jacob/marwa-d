import React, {createRef} from 'react';
import PropTypes from 'prop-types';
import { withStyles } from '@material-ui/core/styles';
import Chip from '@material-ui/core/Chip';
import Button from '@material-ui/core/Button';
import classNames from 'classnames';
// import IconButton from '@material-ui/core/IconButton';
import Edit from '@material-ui/icons/Edit';
import { Table, TableBody, TableCell, TableHead, TableRow } from '@material-ui/core';
import Typography from '@material-ui/core/Typography';
import CircularProgress from '@material-ui/core/CircularProgress';
import { Query, Mutation } from 'react-apollo';
import Dropzone, { useDropzone } from 'react-dropzone';

import ReportOptionsDialog from './ReportOptionsDialog';
// import { UPLOAD_FILE2,  } from '../data/upload';
import { GET_ROOMCONFIGS, UPLOAD_FILE } from '../data/queries';
import {
  DEFAULT_START, DEFAULT_END, DEFAULT_PERIOD, DEFAULT_SECTIONS,
  getStart, getPeriod, getRange, FileStatus
} from '../data/ui_constants';
import { getLocalDateTimeFromUTC, getDateStr, getTimeStr } from '../utils';

const styles = theme => ({
  // root: {
  //   width: '100%',
  //   marginTop: theme.spacing(1),
  //   overflowX: 'auto',
  // },
  // flex: {
  //   // flex: 1,
  // },
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
  uploadLanding: {
    width: 'calc(100% - 6px)',
    height: '200px',
    margin: '0px',
    border: '3px dashed #8b8e94',
    borderRadius: '25px',
    display: 'none',
    [theme.breakpoints.up('lg')]: {
      display: 'block',
      height: '150px',
    },
    [theme.breakpoints.up('xl')]: {
      height: '200px',
    },
  },
  centered: {
    height: '100%',
    width: '100%',
    display: 'table',
  },
  instCont: {
    display: 'table-cell',
    textAlign: 'center',
    verticalAlign: 'middle',
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
  browse: {
    backgroundColor: '#cacbce',
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

const TAG = 'RoomConfig:';

class Upload extends React.Component {
  /**
   * Initialize Component's state using Property Initializer (then no need for constructor).
   * REF: In setState(), prevState is a reference to the previous state. It should not be directly mutated.
   * Instead, changes should be represented by building a new object based on the input from prevState and props.
   * Ref: https://reactjs.org/docs/react-component.html#setstate
   */

  state = {
    test: null,
    open: false,
    selected: {
      groupId: 'def_group',
      roomId: 'def_room',
      reportOptions: {
        source: 'Default Report Options',
        start: DEFAULT_START,
        end: DEFAULT_END,
        period: DEFAULT_PERIOD,
        sections: DEFAULT_SECTIONS
      }
    },
    uploads: [
      // {
      //   source: 'export_12345_10203040_20191001_124520.tar',
      //   sequence: 12345
      //   sn: '10203040'
      //   duration: 30,
      //   start: Date('2019-09-01'),
      //   end: Date('2019-10-01'),
      //   sections: [
      //     Sections.TREND,
      //     Sections.ALARM,
      //     Sections.MONITOR,
      //     Sections.CONFIG_LOG,
      //     Sections.ALARM_LOG,
      //   ]
      // }
    ],
    defaultOptions: {
      source: 'Default Report Options',
      start: DEFAULT_START,
      end: DEFAULT_END,
      period: DEFAULT_PERIOD,
      sections: DEFAULT_SECTIONS
    }
  };

  /**
   * Retrieve the selected room configuration.
   * A room configuration is uniquely identified by groupId + roomId combination, since a unique roomId is only
   * guaranteed within a facility's group!
   */
  getSelectedRoomConfig = (roomConfigs) => {
    const { viewer } = this.props;
    const { selected: { groupId, roomId } } = this.state;
    let config = {};
    if (viewer && groupId && roomId) {
      const { facilityId } = viewer.currentFacilityAndGroup;
      const configFound = roomConfigs.find(x => x.facilityId === facilityId
        && x.groupId === groupId
        && x.roomId === roomId);
      if (configFound) {
        config = configFound;
      }
    }
    return config;
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

  // Accept = (props) => {
  //   const {
  //     getRootProps,
  //     getInputProps,
  //     isDragActive,
  //     isDragAccept,
  //     isDragReject
  //   } = useDropzone({
  //     accept: 'image/jpeg, image/png'
  //   });
  // };

  handleBrowse = () => {
    let hiddenButton = document.getElementById('file');
    hiddenButton.click();
  };

  handleDropList = (acceptedFiles) => {
    console.dir(acceptedFiles);
    for (const value of acceptedFiles) {
      this.addUploadFile(value);
    }
  };

  // handleDropObject = (acceptedFiles) => {
  //   console.dir(acceptedFiles);
  //   for (const [index, value] of acceptedFiles) {
  //     this.addUploadFile(value);
  //   }
  // };

  addUploadFile = value => {

      // Decompose name to get file attributes
      try {

        // Skip invalid files
        let sections = value.name.split('.');
        if ((sections[1] !== 'tar') && (sections[1] !== 'TAR'))
          return;

        // Skip duplicate files
        for (const existing of this.state.uploads) {
          if (existing.name === value.name)
            return;
        }

        // Eventually, check database to see if we processed this already

        // Destructure name
        let parts = sections[0].split('_');
        let sequence = parts[1];
        let sn = parts[2];
        let dateStr = parts[3];
        let year = parseInt(dateStr.slice(0, 4));
        let month = parseInt(dateStr.slice(4, 6)) - 1;
        let day = parseInt(dateStr.slice(6));
        let endDate = new Date(year, month, day);
        let period = this.state.defaultOptions.period;
        let startDate = getStart(endDate, period);
        this.setState({
          uploads: this.state.uploads.concat({
            source: value.name,
            sequence: sequence,
            sn: sn,
            status: FileStatus.EDITING,
            start: startDate,
            end: endDate,
            period: this.state.defaultOptions.period,
            sections: this.state.defaultOptions.sections
          })
        });

        // Handle invalid file name
      } catch(error) {
        console.log("invalid file");
        console.dir(error);
      }
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

  handleUpload = () => {
    console.log("doing a thing.");
    let upList = [...this.state.uploads];
    for( let i = 0; i < upList.length; i++){
      const upload = upList[i];
      if (upload.status === FileStatus.EDITING) {
        upload.status = FileStatus.UPLOADING;
      }
      console.dir(upload.status);
      console.dir(FileStatus.EDITING);
      console.dir(upload);
    }
    this.setState({uploads: upList});
    console.dir(this.state.uploads);
  };

  handleChange = (props, singleUpload) => {
    console.dir(props.target);
    if (props.target.files.length > 0) {
      singleUpload({ variables: {file: props.target.files[0] }}).then(async d => console.log(d))
    }
    this.handleDropList(props.target.files);
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

    // const FileUpload = () => {
    //   return (
    //       <div>
    //         <Mutation mutation={UPLOAD_FILE}>
    //           {singleUpload => (
    //               <form>
    //                 <input type="file" id="file" required onChange={props => this.handleChange(props, singleUpload)}/>
    //               </form>
    //           )}
    //         </Mutation>
    //       </div>
    //   );
    // };

    // const onButtonClick = () => {
    //   // `current` points to the mounted file input element
    //   // inputFile.current.click();
    //   console.dir(inputFile);
    //   // console.log("File " + index.toString() + value.name);
    // };

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
        <div className={classes.uploadLanding}>
          <Dropzone onDrop={acceptedFiles => this.handleDropList(acceptedFiles)} accept='.tar' noClick noKeyboard>
            {({getRootProps, getInputProps}) => (
              <section className={classes.centered}>
                <div className={classes.centered} {...getRootProps()}>
                  <input {...getInputProps()}

                  />
                  <div className={classes.instCont}>
                    <Typography className={classes.instructions} variant='body1' color='inherit' paragraph>
                      Drag files here to upload
                    </Typography>
                    <Typography className={classes.instructions} variant='body1' color='inherit' paragraph>
                      or
                    </Typography>
                    {/*<div>*/}
                    {/*  <Mutation mutation={UPLOAD_FILE}>*/}
                    {/*    {singleUpload => (*/}
                    {/*        <form>*/}
                    {/*          <input type="file" id="file" ref={inputFile} required*/}
                    {/*                 onChange={props => this.handleChange(props, singleUpload)}/>*/}
                    {/*        </form>*/}
                    {/*    )}*/}
                    {/*  </Mutation>*/}
                    {/*</div>*/}
                    <Mutation mutation={UPLOAD_FILE}>
                      {singleUpload => (
                        <input type='file' id='file' style={{display: 'none'}}
                               ref={inputFile} webkitdirectory="" directory="" accept=".tar"
                               onChange={(props) => (this.handleChange(props, singleUpload))}
                               // onChange={({ target: { validity, files: [file] } }) =>
                               //     validity.valid && singleUpload({ variables: { file } })
                               // }
                        />
                      )}
                    </Mutation>
                    <Button className={classNames(classes.browse, classes.muiButton)}
                            onClick={() => (this.handleBrowse())}>
                      BROWSE
                    </Button>
                  </div>
                </div>
              </section>
            )}
          </Dropzone>
        </div>
        <div className={classNames(classes.centered, classes.hideMobile)}>
          <div className={classes.instCont}>
            <Typography className={classes.instructions} variant='body1' color='inherit' paragraph>
              Upload not available on mobile devices
            </Typography>
          </div>
        </div>
        <div className={classes.shadow}>
          <div className={classes.aboveTable}>
            <div className={classes.left}>
              <Button
                  variant='flat'
                  color='primary'
                  aria-label='edit'
                  className={classes.buttonRoom}
                  onClick={() => (this.handleDialogOpen(this.state.defaultOptions))}
                  // identifier={`${n.groupId}_${n.roomId}`}
              >
                <Edit />&nbsp;
                Upload Settings
              </Button>
            </div>
            <div className={classes.right}>
              <Button className={classNames(classes.upload, classes.muiButton)}
                      onClick={() => (this.handleUpload())}>
                UPLOAD
              </Button>
            </div>
            <Typography variant='headline' color='inherit'>
              Upload Queue
            </Typography>
          </div>
          <Table className={classes.table}>
            <TableHead>
              <TableRow className={classes.tableHeader}>
                <TableCell padding={pad} className={classes.tableHeadCell}> </TableCell>
                <TableCell padding={pad} className={classes.tableHeadCell}>Serial Number</TableCell>
                <TableCell padding={pad} className={classes.tableHeadCell}>Copy Date</TableCell>
                <TableCell padding={pad} className={classes.tableHeadCell}>Period</TableCell>
                <TableCell padding={pad} className={classes.tableHeadCell}>Date Range</TableCell>
                <TableCell padding={pad} className={classes.tableHeadCell}>Sections</TableCell>
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

                  if (this.state.uploads.length === 0) {
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
                        {this.state.uploads.map(n => (
                          <TableRow key={n.source}>
                            <TableCell className={classes.xButton}>
                              {(n.status === FileStatus.EDITING) &&
                                <Button
                                    variant='flat'
                                    color='primary'
                                    aria-label='edit'
                                    className={classes.buttonRoom}
                                    onClick={() => (this.handleDelete(n))}
                                >
                                  X
                                </Button>
                              }
                            </TableCell>
                            <TableCell padding={pad} className={classes.editCell}>
                              {(n.status === FileStatus.EDITING) &&
                                <Button
                                    variant='flat'
                                    color='primary'
                                    aria-label='edit'
                                    className={classes.buttonRoom}
                                    onClick={() => (this.handleDialogOpen(n))}
                                    // identifier={`${n.groupId}_${n.roomId}`}
                                >
                                  <Edit />&nbsp;
                                  {n.sn}
                                </Button>
                              }
                              {(n.status !== FileStatus.EDITING) &&
                                n.sn
                              }
                            </TableCell>
                            <TableCell padding={pad} className={classes.tableCell}>{getPeriod(n.end)}</TableCell>
                            <TableCell padding={pad} className={classes.tableCell}>{getPeriod(n.period)}</TableCell>
                            <TableCell padding={pad} className={classes.tableCell}>{getRange(n.start, n.end)}</TableCell>
                            <TableCell padding={pad} className={classes.tableCellLeft}>
                              {n.sections.map((s) => {
                                return <Chip key={s} label={s} className={classes.chip} />;
                              })}
                            </TableCell>
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
        <ReportOptionsDialog
            reportOptions={this.state.selected.reportOptions}
            open={this.state.open}
            onClose={this.handleDialogClose}
            editedBy={viewer.username}
            // roomConfig={this.getSelectedRoomConfig(roomConfigs)}
            riskFactorOptions={facilityRiskFactorOptions}
        />
      </div>
    );
  }
}

Upload.propTypes = {
  classes: PropTypes.object.isRequired,
  theme: PropTypes.object.isRequired,
  viewer: PropTypes.object.isRequired,
  // facilityId: PropTypes.string.isRequired,
};

// NOTE: Use 'withStyles' when you want to provide styles through the Material-UI 'classes' object.
// export default withStyles(styles)(RoomConfig);
export default withStyles(styles, { withTheme: true })(Upload);
// export default withMobileDialog()(withStyles(styles, { withTheme: true })(RoomConfig));
