import React, {createRef} from 'react';
import { withStyles } from '@material-ui/core/styles';
import Button from '@material-ui/core/Button';
import classNames from 'classnames';
import ExpandMoreIcon from '@material-ui/icons/ExpandMore';
import Grid from '@material-ui/core/Grid';
import { Table, TableBody, TableCell, TableHead, TableRow, LinearProgress } from '@material-ui/core';
import Typography from '@material-ui/core/Typography';
import { Query } from 'react-apollo';
import { withApollo } from 'react-apollo';
import Dropzone from 'react-dropzone';
import BrowserList from "../components/BrowserList";
import { isMobile, isChrome, isFirefox, isSafari, isOpera, isEdge, isIE } from 'react-device-detect';
// import md5 from '../components/md5';
import CollapsibleCell from "../components/CollapsibleCell";

import { UPLOAD_FILE, DOWNLOAD_FILE, REPORT_STATUS, RECALL_REPORTS, BATCH_REQUEST, SET_STATUS} from '../data/queries';
import {
  themePalette, ErrorLevel,
  DEFAULT_START, DEFAULT_END, DEFAULT_PERIOD, DEFAULT_SECTIONS, tzCorrect, tzReturn,
  getStart, getRange, getDateStr, FileStatus, PROCESSING_STATUS, OPTIONS_PERIOD, Sections, HOUR_MILLIES
} from '../data/ui_constants';
import { UPLOAD_TIMEOUT_PENDING, UPLOAD_TIMEOUT_UPLOADING, UPLOAD_TIMEOUT_QUEUED, UPLOAD_TIMEOUT_PROCESSING,
  UPLOAD_TIMEOUT_RETRY_DELAY } from '../config';
import ReportOptionsDialog from "./ReportOptionsDialog";
import EmailOptionsDialog from "./EmailOptionsDialog";
import DownloadDialog from "./DownloadDialog";

const styles = theme => ({

  content: {
    width: '100%',
    height: 'calc(70% - 30%)',
    position: 'relative',
    margin: '0 auto',
    paddingTop: '30px',
    // [theme.breakpoints.up('lg')]: {
    //   maxWidth: '940px',
    // },
    // [theme.breakpoints.up('xl')]: {
    //   maxWidth: '1140px',
    // },
  },
  uploadLanding: {
    width: 'calc(100% - 6px)',
    display: 'block',
    height: '340px',
    margin: '0px',
    // border: '3px dashed #8b8e94',
    // borderRadius: '25px',
    [theme.breakpoints.up('sm')]: {
      height: '250px',
    },
    [theme.breakpoints.up('lg')]: {
      height: '260px',
    },
    [theme.breakpoints.up('xl')]: {
      height: '281px',
    },
  },
  mainTitle: {
    fontSize: '22px',
    [theme.breakpoints.up('md')]: {
      fontSize: '28px',
    },
    [theme.breakpoints.up('xl')]: {
      fontSize: '36px',
    },
    fontFamily: '"avenir-black","Segoe UI Black",Roboto,"Helvetica Neue",Arial,sans-serif',
    color: '#57585A',
  },
  tableTitle: {
    zIndex: '-1',
    top: '-5px',
    position: 'relative',
    margin: '0px 37%',
    fontFamily: '"avenir-heavy","Segoe UI Bold",Roboto,"Helvetica Neue",Arial,sans-serif',
  },
  dropGrid: {
    textAlign: 'center',
  },
  fixedHeightGrid: {
    minHeight: 'auto',
    [theme.breakpoints.up('sm')]: {
      minHeight: '130px'
    },
    [theme.breakpoints.up('md')]: {
      minHeight: '140px'
    },
    [theme.breakpoints.up('lg')]: {
      minHeight: '150px'
    }
  },
  instructDiv: {
    position: 'relative',
    margin: '15px 15%',
  },
  blueBar: {
    position: 'absolute',
    top: '464px',
    left: '0px',
    right: '0px',
    height: '65px',
    zIndex: '-1',
    background: theme.palette.primary.main,
    [theme.breakpoints.up('sm')]: {
      top: '374px',
    },
    [theme.breakpoints.up('md')]: {
      top: '379px',
    },
    [theme.breakpoints.up('lg')]: {
      top: '441px',
    },
    [theme.breakpoints.up('xl')]: {
      top: '461px',
    }
  },
  selectBorder: {
    width: '100%',
    margin: '0px',
    borderRadius: 25,
    position: 'relative',
    backgroundColor: theme.palette.background.paper,
    border: '2px solid #a8a9ad',
    transition: theme.transitions.create(['border-color', 'box-shadow']),
    '&:disabled': {
      border: '2px solid #efeff0',
    },
    '&:before': {
      display: 'none',
    },
    '& div::before, div::after': {
      content: 'none',
    },
    '& div': {
      width: '100%',
      paddingRight: '0px !important',
      background: 'none !important',
      '& div': {
        paddingBottom: '0px',
        '&:focus': {
          borderColor: 'white',
        },
      },
      '& input': {
        width: '80%',
        margin: 'auto',
        textAlign: 'center',
      }
    }
  },
  inputText: {
    '& div': {
      '& input': {
        fontSize: '10px',
        fontFamily: '"avenir-roman","Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif',
        [theme.breakpoints.up('sm')]: {
          fontSize: '12px',
        },
        [theme.breakpoints.up('md')]: {
          fontSize: '14px'
        },
        [theme.breakpoints.up('lg')]: {
          fontSize: '16px'
        },
      }
    }
  },
  status: {
    width: '100px',
    margin: 'auto',
    fontFamily: '"avenir-heavy","Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif',
    fontSize: '10px',
    padding: '0pc',
    [theme.breakpoints.up('sm')]: {
      fontSize: '11.5px',
    },
    [theme.breakpoints.up('md')]: {
      fontSize: '16px'
    },
    [theme.breakpoints.up('lg')]: {
      fontSize: '18px'
    }
  },
  dragImg: {
    // width: '200px',
    height: '120px',
    [theme.breakpoints.up('md')]: {
      height: '130px'
    },
    [theme.breakpoints.up('lg')]: {
      height: '140px'
    },
    [theme.breakpoints.up('xl')]: {
      height: '150px'
    }
  },
  downloadImg: {
    height: '35px',
    width: '27px',
    cursor: 'pointer',
    [theme.breakpoints.up('md')]: {
      height: '40px',
      width: '31px',
    },
    [theme.breakpoints.up('md')]: {
      height: '45px',
      width: '35px',
    },
    [theme.breakpoints.up('lg')]: {
      height: '50px',
      width: '39px',
    }
  },
  warnImg: {
    height: '10px',
    width: '10px',
    marginRight: '2px',
    // cursor: 'pointer',
    [theme.breakpoints.up('md')]: {
      height: '16px',
      width: '16px',
    },
    [theme.breakpoints.up('md')]: {
      height: '18px',
      width: '18px',
    },
    [theme.breakpoints.up('lg')]: {
      height: '20px',
      width: '20px',
    }
  },
  warnText: {
    fontFamily: '"avenir-roman","Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif',
    fontSize: '9px',
    marginLeft: '2px',
    position: 'relative',
    top: '-5%',
    [theme.breakpoints.up('md')]: {
      fontSize: '12px',
    },
    [theme.breakpoints.up('md')]: {
      fontSize: '14px',
    },
    [theme.breakpoints.up('lg')]: {
      fontSize: '16px',
    }
  },
  emailImg: {
    height: '35px',
    width: '36px',
    cursor: 'pointer',
    [theme.breakpoints.up('sm')]: {
      height: '45px',
      width: '47px',
    },
    [theme.breakpoints.up('md')]: {
      height: '45px',
      width: '47px',
    },
    [theme.breakpoints.up('lg')]: {
      height: '50px',
      width: '52px',
    }
  },
  messageBox: {
    position: 'absolute',
    width: '220px',
    height: '35px',
    lineHeight: '35px',
    top: '160px',
    left: 'calc(50% - 112px)',
    border: '2px #f1301d solid',
    fontFamily: '"avenir-heavy","Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif',
    fontSize: '24px',
    color: 'white',
    textAlign: 'center',
    borderRadius: '20px',
    filter: "alpha(opacity=0)",
    background: '#f1301d',
    opacity: '0',
    display: 'none'
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
    maxWidth: '350px',
    margin: 'auto',
    position: 'relative',
    color: '#57585A',
    fontFamily: '"avenir-black","Segoe UI Black",Roboto,"Helvetica Neue",Arial,sans-serif',
    fontSize: '14px',
    [theme.breakpoints.up('md')]: {
      fontSize: '16px',
    },
    [theme.breakpoints.up('lg')]: {
      fontSize: '20px',
    }
  },
  orInst: {
    color: '#A8A9AD',
    fontSize: '24px',
    margin: 'auto',
    top: '10px',
    [theme.breakpoints.up('sm')]: {
      top: '70px',
    },
    [theme.breakpoints.up('md')]: {
      fontSize: '33px'
    },
    [theme.breakpoints.up('lg')]: {
      fontSize: '40px'
    }
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
  },
  uploadTable: {
    // boxShadow: '0px 2px 4px 2px #ccc',
    // [theme.breakpoints.down('md')]: {
    //   display: 'none',
    // }
  },
  table: {
    // Mimic Paper
    // backgroundColor: theme.palette.common.white,
    boxShadow: 'none',
    position: 'relative',
    top: '-11px',
    [theme.breakpoints.up('md')]: {
      top: '-7px'
    },
    [theme.breakpoints.up('lg')]: {
      top: '0px'
    }
  },
  tableHeader: {
    // backgroundColor: theme.palette.primary.main,
  },
  tableHeadCell: {
    fontFamily: '"avenir-heavy","Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif',
    textAlign: 'center',
    verticalAlign: 'middle',
    fontSize: '14px',
    padding: '0px',
    height: '65px',
    color: theme.palette.common.white,
    margin: 0,
    // padding: theme.spacing.unit / 2,
    // padding: '4px',
    [theme.breakpoints.up('sm')]: {
      fontSize: '17px',
    },
    [theme.breakpoints.up('md')]: {
      fontSize: '20px'
    },
    [theme.breakpoints.up('lg')]: {
      fontSize: '22px'
    }
  },
  tableCell: {
    height: 'auto',
    textAlign: 'center',
    margin: 0,
    padding: theme.spacing(0.5),
  },
  tableCellLeft: {
    height: 'auto',
    textAlign: 'left',
    margin: 0,
    padding: theme.spacing(0.5),
    paddingLeft: '10px',
  },
  topHeader: {
    clear: 'both',
    margin: '0px'
  },
  autoHeight: {
    height: 'auto',
  },
  button: {
    margin: 0,
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
  arrowCell: {
    verticalAlign: 'top',
    paddingTop: '6px'
  },
  collapseArrow: {
    transition: 'transform 0.1s ease-out',
    paddingTop: '6px'
  },
  chip: {
    margin: 2,
    fontSize: '12px',
  },
  progress: {
    margin: `0 ${theme.spacing(0.5)}px`,
  },
  muiButton: {
    fontFamily: '"avenir-heavy","Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif',
    fontSize: '16px',
    fontStyle: 'normal',
    margin: '0px 24px 12px 24px',
    color: 'white',
  },
  blueButton: {
    color: 'white',
    background: theme.palette.primary.main,
    '&:disabled': {
      color: 'white',
    }
  },
  orangeButton: {
    borderRadius: '50px',
    fontFamily: '"avenir-heavy","Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif',
    fontStyle: 'normal',
    textTransform: 'capitalize',
    color: 'white',
    backgroundColor: theme.palette.ternary.main,
    // This is experimental
    '&:hover': {
      backgroundColor: theme.palette.ternary.light,
      // Reset on touch devices, it doesn't add specificity
      '@media (hover: none)': {
        // This toggles after clicks
        backgroundColor: theme.palette.secondary.dark,
      },
    },
    '&:disabled': {
      color: theme.palette.disabled.light,
      backgroundColor: theme.palette.disabled.dark,
    }
  },
  browse: {
    marginTop: '15px',
    marginBottom: '5px',
    fontSize: '24px',
    padding: '0px 30px',
    [theme.breakpoints.up('sm')]: {
      marginTop: '55px',
      marginBottom: '0px',
      fontSize: '28px',
      padding: '0px 35px',
    },
    [theme.breakpoints.up('md')]: {
      fontSize: '28px',
      padding: '0px 35px',
    },
    [theme.breakpoints.up('lg')]: {
      fontSize: '32px',
      padding: '0px 40px',
    }
  },
  midButton: {
    fontSize: '14px',
    padding: '0px 16px',
    [theme.breakpoints.up('sm')]: {
      fontSize: '18px',
      padding: '0px 20px',
    },
    [theme.breakpoints.up('md')]: {
      fontSize: '18px',
      padding: '0px 24px',
    },
    [theme.breakpoints.up('lg')]: {
      fontSize: '22px',
      padding: '0px 28px',
    }
  },
  medSmallButton: {
    fontSize: '11px',
        padding: '2px 12px',
        margin: '0px',
        lineHeight: '22px',
        [theme.breakpoints.up('sm')]: {
      fontSize: '13px',
          padding: '2px 14px',
    },
    [theme.breakpoints.up('md')]: {
      fontSize: '15px',
          padding: '3px 16px',
    },
    [theme.breakpoints.up('lg')]: {
      fontSize: '18px',
          padding: '3px 20px',
    }
  },
  smallButton: {
    fontSize: '11px',
    padding: '0px 6px',
    margin: '0px',
    lineHeight: '22px',
    [theme.breakpoints.up('sm')]: {
      fontSize: '13px',
      padding: '0px 8px',
    },
    [theme.breakpoints.up('md')]: {
      fontSize: '15px',
      padding: '0px 10px',
    },
    [theme.breakpoints.up('lg')]: {
      fontSize: '18px',
      padding: '0px 12px',
    }
  },
  downloadAllButton: {
    float: 'right',
    fontSize: '14px',
    backgroundColor: '#cacbce',
    margin: '0px 24px 5px 0px',
  },
  clearQueueButton: {
    float: 'left',
    margin: '0px 0px 5px 24px',
  },
  uploadButton: {
    float: 'right',
    margin: '0px 24px 5px 0px',
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
    },
  },
  viewTab: {
    float: 'left',
    top: '15px',
    borderRadius: '10px 10px 0 0',
    minHeight: '24px',
    margin: '0 2.5px',
    padding: '0px 20px',
    color: 'white',
    fontSize: '12px',
    textTransform: 'none',
    fontStyle: 'normal',
    fontFamily: '"avenir-heavy","Segoe UI Bold",Roboto,"Helvetica Neue",Arial,sans-serif',
    [theme.breakpoints.up('md')]: {
      fontSize: '14px',
      top: '18px',
      minHeight: '26px',
    },
    [theme.breakpoints.up('lg')]: {
      fontSize: '18px',
      top: '20px',
      minHeight: '30px',
    },
  },
  noUploads: {
    textAlign: 'center',
    marginTop: '5px',
    paddingTop: '15px',
    fontSize: '16px',
    [theme.breakpoints.up('md')]: {
      fontSize: '18px',
    },
    [theme.breakpoints.up('lg')]: {
      fontSize: '20px',
    },
  },
  right: {
    float: 'right',
    marginLeft: '40px'
  },
  left: {
    float: 'left',
    marginLeft: '20px'
  },
  medUpOnly: {
    display: 'none',
    [theme.breakpoints.up('md')]: {
      display: 'inherit',
    },
  },
  smlDnOnly: {
    display: 'inherit',
    [theme.breakpoints.up('md')]: {
      display: 'none',
    },
  },
  noIEFlex: {
    [theme.breakpoints.down('xs')]: {
      display: 'block',
    },
  }
});

// Request report list from server on page reload
const recallReports = async (page) => {

  // Lookup report list for upload page
  let sessionID = localStorage.getItem('sessionID') || "";
  let accessKey = localStorage.getItem('accessKey') || "";
  let snList = JSON.parse(localStorage.getItem('snList')) || "";
  let reportIdList = JSON.parse(localStorage.getItem('reportIdList')) || "";
  let fileNameList = JSON.parse(localStorage.getItem('fileNameList')) || "";

  // Request details from server
  let result = null;
  if (reportIdList !== "") {
    try {
      const { data } = await page.props.client.query({
        query: RECALL_REPORTS,
        variables: { sessionID, accessKey, snList, reportIdList }
      });
      result = data;

    } catch (error) {
      console.dir(error);
      console.log("Error: Unable to get download URI for file.");
    }
  }
  if ((result === null) || (result.recallReports === null))
    return;

  // Populate reports in page state
  let uploads = [];
  let timerNeeded = false;
  for (let upload of result.recallReports) {

    // Construct section list
    let sections = [];
    let sectionsIdx = JSON.parse(upload.sections);
    for (let section of sectionsIdx) {
      let idx = parseInt(section, 10);
      for (let def of Object.values(Sections)) {
        if (def.code === idx)
          sections.push(def);
      }
    }

    if (upload.uri === undefined)
      upload.uri = "";
    let queuedStart = (upload.status === FileStatus.QUEUED) ? Date.now() : null;
    let processingStart = (upload.status === FileStatus.PROCESSING) ? Date.now() : null;
    let upload_item = {
      source: "",
      reportID: upload.reportID,
      sequence: "",
      label: upload.label,
      sn: upload.sn,
      status: upload.status,
      start: tzReturn(new Date(upload.reportStart * 1000)),
      end: tzReturn(new Date(upload.reportEnd * 1000)),
      export: tzReturn(new Date(upload.exportDate * 1000)),
      progress: 1,
      period: OPTIONS_PERIOD.find(x => x.hours === parseInt(upload.reportHours, 10)),
      sections,
      uri: upload.uri,
      errorLevel: upload.errorLevel,
      pendingStart: null,
      queuedStart: queuedStart,
      processingStart: processingStart,
      uploadRetries: 0
    };
    for (let i = 0; i < fileNameList.length; i++) {
      if (reportIdList[i] === upload.reportID)
        upload_item.source = fileNameList[i];
    }
    uploads.push(upload_item);
    if ([FileStatus.PENDING, FileStatus.UPLOADING, FileStatus.QUEUED, FileStatus.PROCESSING].includes(upload.status))
      timerNeeded = true;
  }
  page.setState({ uploads, view: ViewStates.DATE });
  page.setState(updateAllUploads(uploads));
  let tab = document.getElementById("SerTab");
  tab.click();
  if (timerNeeded)
    page.startUpdateTimer();
};

// Save session information before leaving page
const saveSession = (page) => {

  // Abort if page reference failed
  if (page === null)
    return;

  // Prepare items to save
  let reportIdList = [];
  let fileNameList = [];
  let snList = [];
  for (let upload of page.state.uploads) {
    reportIdList.push(upload.reportID);
    fileNameList.push(upload.source);
    snList.push(upload.sn);
  }

  // Lookup report list for upload page
  localStorage.setItem('snList', JSON.stringify(snList));
  localStorage.setItem('reportIdList', JSON.stringify(reportIdList));
  localStorage.setItem('fileNameList', JSON.stringify(fileNameList));
  console.log("Saved session.");
};

// It takes this to colorize an MUI progress bar with custom colors
const DisabledProgress = withStyles({
  colorPrimary: {
    backgroundColor: themePalette.palette.disabled.main,
  },
  barColorPrimary: {
    backgroundColor: themePalette.palette.disabled.light,
  },
})(LinearProgress);

const ProcessingProgress = withStyles({
  colorPrimary: {
    backgroundColor: "#f1d027",
  },
  barColorPrimary: {
    backgroundColor: "#f9ea9f",
  },
})(LinearProgress);

const ErrorProgress = withStyles({
  colorPrimary: {
    backgroundColor: themePalette.palette.error.main,
  },
  barColorPrimary: {
    backgroundColor: themePalette.palette.error.main,
  },
})(LinearProgress);

function addUploads(uploadList) {
  return (previousState, currentProps) => {
    // return { uploads: [...previousState.uploads, ...uploadList], do_poll: true};
    return { uploads: [...previousState.uploads, ...uploadList]};
  };
}

function updateUpload(upload) {
  return (previousState, currentProps) => {
    let do_poll = false;
    previousState.uploads.forEach((exUpload, idx) => {
      if (exUpload.source === upload.source)
        previousState.uploads[idx] = upload;
      if ([FileStatus.QUEUED, FileStatus.PROCESSING, FileStatus.PENDING].includes(previousState.uploads[idx].status))
        do_poll = true;
    });
    return { uploads: previousState.uploads, do_poll};
  };
}

function updateAllUploads(uploads) {
  let do_poll = false;
  return (previousState, currentProps) => {
    previousState.uploads.forEach((exUpload, idx) => {
      uploads.forEach((newUpload) => {
        if (exUpload.source === newUpload.source)
          previousState.uploads[idx] = newUpload;
      });
      if ([FileStatus.QUEUED, FileStatus.PROCESSING, FileStatus.PENDING].includes(previousState.uploads[idx].status))
        do_poll = true;
    });
    return { uploads: previousState.uploads, do_poll };
  };
}

function updateExpansion(key, value, disableTransitions=false, pageComponent=null) {
  if (disableTransitions)
    pageComponent.enableTransition(false);
  return (previousState, currentProps) => {
    previousState.groupExpansion[key] = value;
    return { groupExpansion: previousState.groupExpansion};
  };
}

const copyUpload = (old) => {
  return {
    source: old.source,
    reportID: old.reportID,
    sequence: old.sequence,
    label: old.label,
    sn: old.sn,
    size: old.size,
    status: old.status,
    start: old.start,
    end: old.end,
    export: old.export,
    fileEnd: old.fileEnd,
    progress: old.progress,
    period: old.period,
    sections: old.sections,
    uri: old.uri,
    acceptedFile: old.acceptedFile,
    errorLevel: old.errorLevel,
    pendingStart: old.pendingStart,
    queuedStart: old.queuedStart,
    processingStart: old.processingStart,
    uploadRetries: old.uploadRetries
  };
};

const ViewStates = {
  SERIAL: 1,
  DATE: 2
};

// Poll the database and check for report status updates
// React postpones processing this when response is unchanged,
//   so http requests occur regularly, but the callback occurs sporadically.
const ReportStatus = ({ component, snList, reportIdList, do_poll }) => (
    <Query
        query={REPORT_STATUS}
        variables={{ snList, reportIdList }}
        skip={do_poll !== true}
        pollInterval={ do_poll? 1000 : 0 }
        fetchPolicy="network-only"
    >
      {({ loading, error, data }) => {

        // Store references
        let page = component;
        if ("page" in component)
          page = component.page;
        this.page = page;

        // Only run when data available
        if (loading) return null;
        if (error) {
          console.log(error);
          return null;
        }
        if (data === undefined) return null;

        // Reset session timer so countdown doesn't start until all files are processed
        page.resetSessionTimer();

        // Process changes
        return <div id="dataBasket" style={{ display: 'none' }}>
          { (updateState(page, data) && true) && " " }
        </div>;
      }}
    </Query>
);

// This is a hack to trigger a general function once the report status query completes.
const updateState = (page, data) => {

  // Pair report records and update
  let changes = [];
  for (let old_key in page.state.uploads) {
    const old_item = page.state.uploads[old_key];
    for (let new_key in data.reportStatus) {
      const new_item = data.reportStatus[new_key];
      if ((old_item.reportID === new_item.reportID) && (old_item.status !== new_item.status)) {

        // Completed - trigger file link request and update later
        if (new_item.status === FileStatus.COMPLETE) {
          DownloadFile(page, page.props.sessionID, page.props.accessToken, old_item.sn, new_item.reportID, new_item.errorLevel);

        // Other states - update now
        } else {
          let new_upload = copyUpload(old_item);

          // Set processing start time
          if (new_item.status === FileStatus.PROCESSING)
            new_upload.processingStart = Date.now();

          // Update states
          new_upload.status = new_item.status;
          new_upload.errorLevel = new_item.errorLevel;
          changes.push(new_upload);
        }

      }
    }
  }
  // Update states at once
  if (changes.length > 0)
    page.setState(updateAllUploads(changes));

  return "name";
};

// Request file download link
const DownloadFile = async ( page, sessionID, accessKey, sn, reportID, errorLevel ) => {

  // Vars and references
  this.page = page;
  let status = FileStatus.ERROR;
  let result = null;

  // Request download URI
  try {
    const { data } = await page.props.client.query({
      query: DOWNLOAD_FILE,
      variables: { session: sessionID, accessKey, sn, reportID }
    });
    result = data;

    // Only run when data available
    if ((result !== null) && (result.reportDownload !== null))
      status = FileStatus.COMPLETE;

  } catch (error) {
    console.dir(error);
    console.log("Error: Unable to get download URI for file.");
  }

  // Pair report records and update
  for (let old_key in page.state.uploads) {
    const old_item = page.state.uploads[old_key];
    if (old_item.reportID === reportID) {
      let new_item = copyUpload(old_item);

      // Update status and download URI
      new_item.status = status;
      new_item.errorLevel = errorLevel;
      if (status === FileStatus.COMPLETE) {
        const uri = result.reportDownload;
        new_item.uri = uri;
      }

      // Update states at once
      page.setState(updateUpload(new_item));
      saveSession(page);
    }
  }
};

// const TAG = 'GuestUpload:';
const maxUploads = 2;


class GuestUpload extends React.Component {
  /**
   * Initialize Component's state using Property Initializer (then no need for constructor).
   * REF: In setState(), prevState is a reference to the previous state. It should not be directly mutated.
   * Instead, changes should be represented by building a new object based on the input from prevState and props.
   * Ref: https://reactjs.org/docs/react-component.html#setstate
   */
  constructor(props) {
    super(props);
    this.useValLanding = props.useValLanding;
    this.updateTimer = null;
    this.selectedFiles = [];
    this.statePending = false;
    this.lastPoll = Date.now();
    this.uploadStatusQueue = {};
    this.resetSessionTimer = props.resetTimer;
  };
  state = {
    view: ViewStates.SERIAL,
    emailOpen: false,
    optionsOpen: false,
    downloadOpen: false,
    emailRecordID: null,
    emailRecordSN: null,
    emailInputFileName: null,
    emailInputFileType: null,
    batchID: null,
    batchURI: "",
    zipLink: "",
    selectedFiles: [],
    selected: {
      groupId: 'def_group',
      roomId: 'def_room',
      reportOptions: {
        source: 'Default Report Options',
        reportID: "",
        start: DEFAULT_START,
        end: DEFAULT_END,
        export: DEFAULT_END,
        period: DEFAULT_PERIOD,
        progress: 0,
        sections: DEFAULT_SECTIONS,
        status: FileStatus.EDITING
      }
    },
    uploads: [
      // { Format will look like this
      //   source: 'export_12345_10203040_20191001_124520.tar',
      //   reportID: '',
      //   sequence: 12345,
      //   label: '',
      //   sn: '10203040',
      //   size: 0,
      //   duration: 30,
      //   start: Date('2019-09-01'),
      //   end: Date('2019-10-01'),
      //   export: Date('2019-10-01'),
      //   fileEnd: Date('2019-10-01'),
      //   sections: [
      //     Sections.TREND,
      //     Sections.ALARM,
      //     Sections.MONITOR,
      //     Sections.CONFIG_LOG,
      //     Sections.ALARM_LOG,
      //   ]
      //   uri: ''
      //   errorLevel: 0,
      //   pendingStart: null
      //   queuedStart: null,
      //   processingStart: null,
      //   uploadRetries: 0
      // }
    ],
    activeOptions: {
      source: 'Default Report Options',
      start: DEFAULT_START,
      end: DEFAULT_END,
      period: DEFAULT_PERIOD,
      sections: DEFAULT_SECTIONS
    },
    defaultOptions: {
      source: 'Default Report Options',
      start: DEFAULT_START,
      end: DEFAULT_END,
      period: DEFAULT_PERIOD,
      sections: DEFAULT_SECTIONS
    },
    emailFiles: [],
    sortBy: "serial",
    snIndexed: false,
    dateIndexed: false,
    snIndexList: [],
    dateIndexList: [],
    snGroupLength: {},
    dateGroupLength: {},
    groupExpansion: {},
    emailFileName: '',
    transitions: false,
    do_poll: false
  };

  // Functions on load
  componentDidMount = () => {
    if (this.useValLanding)
      recallReports(this);
    window.addEventListener('load', async () => { recallReports(this) });
    window.addEventListener('beforeunload', this.beforeunload.bind(this));
  };

  // Functions on exit
  componentWillUnmount() {
    //window.removeEventListener("beforeunload", function () { saveSession(this) });
    window.removeEventListener('beforeunload', this.beforeunload.bind(this));
  }

  // Check with user before leaving during upload
  beforeunload(e) {
    let uploading = false;
    for (let upload of this.state.uploads) {
      if ((upload.status === FileStatus.UPLOADING) || (upload.status === FileStatus.EDITING))
        uploading = true;
    }
    if (uploading) {
      e.preventDefault();
      e.returnValue = true;
    }
  }

  handleBrowse = async () => {
    let hiddenButton = document.getElementById('file');
    hiddenButton.click();
  };

  handleDropList = (acceptedFiles) => {

    // // Mutation reference
    // this.singleUpload = singleUpload;

    // No action on change to blank input (for IE)
    if (acceptedFiles.length === 0) {
      return;
    }

    // Filter files
    // let someInvalid = false;
    let someOld = false;
    this.selectedFiles = [];
    for (const fileName of acceptedFiles) {
      try {

        // Read file modified date
        // Returns undefined in IE or Safari
        // const modDate = fileName.lastModified;

        // Skip invalid files
        let sections = fileName.name.split('.');
        if ((sections[1] !== 'tar') && (sections[1] !== 'TAR')) {
          // someInvalid = true;
          continue;
        }

        // Skip duplicate files
        let found = false;
        for (const existing of this.state.uploads.concat(this.selectedFiles)) {
          if (existing.source === fileName.name) {
            found = true;
            break;
          }
        }
        if (found) {
          someOld = true;
          continue;
        }

        // // Generate MD5 hash
        // let fileBytes = // This requires async file buffering
        // let hash = mk5(fileBytes);

        // Destructure name
        let item = {};
        item.source = fileName.name;
        item.reportID = "";
        item.status = FileStatus.EDITING;
        item.progress = 0;
        item.label = "";
        item.size = fileName.size;
        let numName = sections[0].replace('export_','');
        numName = numName.replace(/[a-zA-Za-zA-Z]/g,'');
        let parts = numName.split('_');
        item.sequence = parts[0];
        item.sn = parts[1];
        let ds = parts[2];
        let ts = parts[3];
        item.dateStr = ds;
        item.timeStr = parts[3];
        let year = parseInt(ds.slice(0, 4), 10);
        let month = parseInt(ds.slice(4, 6), 10) - 1;
        let day = parseInt(ds.slice(6), 10);
        let hour = parseInt(ts.slice(0, 2), 10);
        let minute = parseInt(ts.slice(2, 4), 10);
        let second = parseInt(ts.slice(4), 10);
        let refDate = new Date(year, month, day, hour, minute, second);

        // // Enable this to anchor report to modified date
        // // Only works in Chrome, Firefox, Edge, and Opera
        // if (typeof modDate !== 'undefined') {
        //   refDate = new Date(modDate);
        // }

        item.end = refDate;
        item.export = item.end;
        item.fileEnd = item.end;
        item.period = this.state.defaultOptions.period;
        item.sections = this.state.defaultOptions.sections;
        item.start = getStart(item.end, item.period);
        item.uri = "";
        item.acceptedFile = fileName;
        item.errorLevel = 0;
        item.pendingStart = Date.now();
        item.queuedStart = null;
        item.processingStart = null;
        item.uploadRetries = 0;

        // Check for required fields
        let invalidFields = false;
        invalidFields = item.sn === "" || invalidFields;
        invalidFields = ds === "" || invalidFields;
        if (invalidFields) {
          // someInvalid = true;
          continue;
        }

        // Save file information
        this.selectedFiles.push(item);

      // Catch mis-named files as invalid
      } catch (e) {
        console.log("Invalid file: " & fileName);
      }
    }

    // Reset input field
    let hiddenButton = document.getElementById('file');
    hiddenButton.value = "";

    // No new and valid files found
    if (this.selectedFiles.length === 0) {
      if (someOld) {
        this.uploadMessage("Already Uploaded");
      } else {
        this.uploadMessage("No Valid Files");
      }
      return;
    }

    // Prepare default options
    let defaults = copyUpload(this.state.defaultOptions);

    // Show report options dialog for file batch
    this.setState({optionsOpen: true, activeOptions: defaults});
  };

  // Get function for list of uploads to edit
  getSelectedFiles = () => {
    return this.selectedFiles;
  };

  // Update options from dialog
  updateOptions = (options) => {

    // Close options dialog
    this.closeOptions();

    // Process changes
    let fileList = this.selectedFiles;
    for (const file of fileList) {
      file.sections = options.sections;
      if (options.from === "Export") {
        file.end = file.export;
        file.start = new Date(file.end.getTime() - options.period.hours * HOUR_MILLIES);
      } else {
        file.start = options.start;
        file.end = options.end;
      }
      file.period = options.period;
      file.status = FileStatus.EDITING;
      file.sections = options.sections;
    }

    // Pass function, not value. Ensures repeated async call doesn't overwrite earlier values.
    this.setState(addUploads(fileList), () => {

      // Re-index rows
      // do_poll will enable update timer, which also starts uploads
      // Reset batch ID and URI
      this.setState({dateIndexed: false, snIndexed: false, batchID: null, batchURI: ""});
      this.sortUploads(this.state.sortBy);
    });

  };

  // Status update timer
  startUpdateTimer = () => {

    // Update status and start uploads when possible
    this.updateTimer = setInterval(() => {
      let updateNeeded = false;
      let stopUpdate = true;
      let uploads = this.state.uploads;

      // Count active uploads
      let activeUploads = 0;
      for (let upload of uploads) {
        if (upload.status === FileStatus.UPLOADING)
          activeUploads += 1;
      }

      // Start new uploads up to max concurrency
      if (activeUploads < maxUploads) {
        for (let upload of uploads) {

          // Look for pending uploads
          if ((upload.status === FileStatus.PENDING) && (activeUploads < maxUploads)) {
            updateNeeded = true;

            // Prepare section list
            let sections = [];
            for (let def of upload.sections) {
              sections.push(def.code);
            }

            // Start new uploads
            console.log("Starting new upload: " + upload.source);
            activeUploads += 1;
            upload.status = FileStatus.UPLOADING;
            this.props.uploadClient.mutate({
              mutation: UPLOAD_FILE,
              variables: {
                sessionID: this.props.sessionID,
                file: upload.acceptedFile,
                start: Math.round(tzCorrect(upload.start).getTime() / 1000),
                end: Math.round(tzCorrect(upload.end).getTime() / 1000),
                hours: upload.period.hours,
                sections: JSON.stringify(sections),
                label: upload.label,
                size: upload.size,
                sn: upload.sn,
                exportDate: Math.round(tzCorrect(upload.export).getTime() / 1000),
                uploadDate: Math.round(tzCorrect(new Date()).getTime() / 1000),
              },
              context: {
                fetchOptions: {
                  useUpload: true,
                  onProgress: (ev) => {
                    try {
                      this.uploadStatusQueue[upload.acceptedFile.name] = ev.loaded / ev.total;
                    } catch (err) {
                      console.log("error");
                      console.dir(err);
                    }
                  }
                }
              }
            }).then(async d => {
              upload.queuedStart = Date.now();
              upload.processingStart = null;
              upload.reportID = d.data.singleUpload.reportID;
              upload.status = parseInt(d.data.singleUpload.status, 10);
              this.setState(updateUpload(upload), () => this.enableTransition(true));
              saveSession(this);
              console.log("Uploaded file: " + upload.source);
            }).catch(async e => {
              this.setState(updateUpload(upload), () => this.enableTransition(true));
              console.log("Error while uploading file.", upload.source, upload.status);
              console.dir(e);

              // Check for recent status updates like
              for (let current_upload of this.state.uploads) {
                if (current_upload.source === upload.source)
                  upload.source = current_upload.source;
              }

              // Restart upload after wait
              if (upload.uploadRetries <3 && upload.status !== FileStatus.ERROR) {
                console.log("Waiting to retry.", UPLOAD_TIMEOUT_RETRY_DELAY);
                upload.progress = 0;
                upload.uploadRetries += 1;
                upload.queuedStart = null;
                upload.processingStart = null;
                upload.status = FileStatus.RETRYING;
                this.setState(updateUpload(upload));
                setTimeout((error) => {
                  console.dir(error);
                  console.log("Restarting Upload.");
                  upload.status = FileStatus.PENDING;
                  this.setState(updateUpload(upload));
                }, UPLOAD_TIMEOUT_RETRY_DELAY * 1000)

              // Set error status and abort after 3 tries
              } else {
                upload.status = FileStatus.ERROR;
                this.setState(updateUpload(upload), () => this.enableTransition(true));
                console.log("Error: Unable to upload file after 3 attempts.");
              }
            });
          }
        }
      }

      // Get session authentication
      let sessionID = localStorage.getItem('sessionID') || "";
      let accessKey = localStorage.getItem('accessKey') || "";

      // Per-upload operations
      for (let upload of uploads) {

        // Timeout pending item
        if ((upload.pendingStart !== null) && (upload.status === FileStatus.PENDING)) {
          if (Date.now() - upload.pendingStart > (UPLOAD_TIMEOUT_PENDING - 2) * 1000) {
            upload.status = FileStatus.ERROR;
            updateNeeded = true;
            console.log("Error: File not uploaded in expected time period.");
          }
        }

        // Timeout uploading item
        // Normally uploads will timeout as a network error this is a backup
        else if ((upload.pendingStart !== null) && (upload.status === FileStatus.UPLOADING)) {
          if (Date.now() - upload.pendingStart > (UPLOAD_TIMEOUT_PENDING + UPLOAD_TIMEOUT_UPLOADING) * 1000) {
            upload.status = FileStatus.ERROR;
            updateNeeded = true;
            this.props.client.mutate({
              mutation: SET_STATUS,
              variables: { sessionID, accessKey, snList: [upload.sn], reportIdList: [upload.reportID],
                statusList: [FileStatus.ERROR] }
            }).catch (error => {
              console.dir(error);
              console.log("Error: File not processed in expected time period.");
            })
          }
        }

        // Timeout queued item
        else if ((upload.queuedStart !== null) && (upload.status === FileStatus.QUEUED)) {
          if (Date.now() - upload.queuedStart > UPLOAD_TIMEOUT_QUEUED * 1000) {
            upload.status = FileStatus.ERROR;
            updateNeeded = true;
            this.props.client.mutate({
              mutation: SET_STATUS,
              variables: { sessionID, accessKey, snList: [upload.sn], reportIdList: [upload.reportID],
                statusList: [FileStatus.ERROR] }
            }).catch (error => {
              console.dir(error);
              console.log("Error: File not processed in expected time period.");
            })
          }
        }

        // Timeout processing
        else if ((upload.processingStart !== null) && (upload.status === FileStatus.PROCESSING)) {
          if (Date.now() - upload.processingStart > UPLOAD_TIMEOUT_PROCESSING * 1000) {
            upload.status = FileStatus.ERROR;
            updateNeeded = true;
            this.props.client.mutate({
              mutation: SET_STATUS,
              variables: { sessionID, accessKey, snList: [upload.sn], reportIdList: [upload.reportID],
                statusList: [FileStatus.ERROR] }
            }).catch (error => {
              console.dir(error);
              console.log("Error: Unable to update report status to error.");
            })
          }
        }

        // Determine if timer should stop
        if (this.statePending || updateNeeded || ![FileStatus.ERROR, FileStatus.COMPLETE].includes(upload.status))
          stopUpdate = false;

        // Update progress on screen
        if (upload.acceptedFile !== undefined) {
          let newProgress = this.uploadStatusQueue[upload.acceptedFile.name];
          if (newProgress !== undefined) {
            if (upload.progress !== newProgress) {
              upload.progress = newProgress;
              updateNeeded = true;
            }
          }
        }
      }

      // Update states
      if (updateNeeded) {
        this.statePending = true;
        this.setState(
          updateAllUploads(uploads), () => {this.statePending = false})}

      // Stop timer
      if (stopUpdate)
        this.stopUpdateTimer();
    }, 250);
  };

  // Status update timer
  stopUpdateTimer = () => {
    if (this.updateTimer !== null)
      clearTimeout(this.updateTimer);
  };

  // Upload options accepted
  beginUpload = () => {

    // Process changes
    let haveUploads = false;
    let fileList = this.state.uploads;
    for (const file of fileList) {
      if (file.status === FileStatus.EDITING) {
        file.status = FileStatus.PENDING;
        file.pendingStart = Date.now();
        haveUploads = true;
      }
    }

    // Pass function, not value. Ensures repeated async call doesn't overwrite earlier values.
    if (haveUploads) {
      console.log("starting upload 1");
      this.setState(updateAllUploads(fileList), () => {

        // do_poll will enable update timer, which also starts uploads
        // Reset batch ID and URI
        this.setState({do_poll: true, batchID: null, batchURI: ""});
        this.startUpdateTimer();
      });
    }
  };

  // Show upload message. It appears, then fades
  uploadMessage = (message) => {
    let messageBox = document.getElementById("message-box");
    messageBox.innerText = message;
    messageBox.style.transition = 'none';
    messageBox.style.filter = 'alpha(opacity=70)';
    messageBox.style.opacity = '0.7';
    messageBox.style.display = 'block';
    setTimeout(function() {
      messageBox.style.transition = 'opacity 2s';
      messageBox.style.opacity = '0';
    }, 1250);
    setTimeout(function() {
      messageBox.style.display = 'none';
    }, 3250);
  };

  // Sorts rows based on tab selection
  // Also generate grouping indexes to control group expansion
  sortUploads = (field) => {
    let result = false;
    this.enableTransition(false);
    this.setState({sortBy: field});
    if (field === "date") {
      this.setState({view: ViewStates.DATE}, () => this.enableTransition(true));
      result = this.sortDate();
    } else if (field === "serial") {
      this.setState({view: ViewStates.SERIAL}, () => this.enableTransition(true));
      result = this.sortSN();
    } else
      this.enableTransition(true);
    // this.enableTransition(true);
    return result;
  };

  sortDate = async () => {
    await this.setState(prevState => {
      this.state.uploads.sort((a, b) => ((a.export === b.export) ? (a.sn - b.sn) : a.export - b.export));
    });
    if (!this.state.dateIndexed) {
      let groupIndexList = [];
      let groupLength = {};
      let lastGroup = "";
      let lastIndex = 0;
      let groupCount = 0;
      for (let idx=0; idx < this.state.uploads.length; idx++) {
        let upload = this.state.uploads[idx];
        groupCount++;
        if (!(upload.export.toString() in this.state.groupExpansion))
          this.setState(updateExpansion(upload.export, true, true, this));
        if (upload.export.toString() !== lastGroup.toString()) {
          lastGroup = upload.export;
          groupIndexList.push(idx);
          if (idx !== 0)
            groupLength[lastIndex] = groupCount;
          lastIndex = idx;
          groupCount = 0;
        }
        if (idx === (this.state.uploads.length - 1))
          groupLength[lastIndex] = groupCount + 1;
      }
      await this.setState({dateIndexList: groupIndexList, dateGroupLength: groupLength, dateIndexed: true});
    }
    return true;
  };

  sortSN = async () => {
    await this.setState(prevState => {
      this.state.uploads.sort((a, b) => ((a.sn === b.sn) ? (a.export - b.export) : a.sn - b.sn));
    });
    if (!this.state.snIndexed) {
      let groupIndexList = [];
      let groupLength = {};
      let lastGroup = "";
      let lastIndex = 0;
      let groupCount = 0;
      for (let idx=0; idx < this.state.uploads.length; idx++) {
        let upload = this.state.uploads[idx];
        groupCount++;
        if (!(upload.sn in this.state.groupExpansion))
          this.setState(updateExpansion(upload.sn, true, true, this));
        if (upload.sn !== lastGroup) {
          lastGroup = upload.sn;
          groupIndexList.push(idx);
          if (idx !== 0)
            groupLength[lastIndex] = groupCount;
          lastIndex = idx;
          groupCount = 0;
        }
        if (idx === (this.state.uploads.length - 1))
          groupLength[lastIndex] = groupCount + 1;
      }
      await this.setState({snIndexList: groupIndexList, snGroupLength: groupLength, snIndexed: true});
    }
    return true;
  };

  isFirstInGroup = (idx) => {
    if (this.state.sortBy === "date")
      return this.state.dateIndexList.includes(idx);
    else if (this.state.sortBy === "serial")
      return this.state.snIndexList.includes(idx);
  };

  isSingle = (idx) => {
    if (this.state.sortBy === "date")
      return (this.state.dateIndexList.includes(idx) && (this.state.dateGroupLength[idx] > 1));
    else if (this.state.sortBy === "serial")
      return (this.state.snIndexList.includes(idx) && (this.state.snGroupLength[idx] > 1));
  };

  setVisibility = (upload) => {
    this.enableTransition(true);
    if (this.state.sortBy === "date") {
      let state = this.state.groupExpansion[upload.export.toString()];
      this.setState(updateExpansion(upload.export, !state));
    }
    if (this.state.sortBy === "serial") {
      let state = this.state.groupExpansion[upload.sn];
      this.setState(updateExpansion(upload.sn, !state));
    }
  };

  enableTransition = (enable) => {
    let components = document.querySelectorAll("[class^=CollapsibleCell]");
    components = [...components, ...document.querySelectorAll("[class*=collapseArrow]")];
    components = [...components, ...document.querySelectorAll("[class*=collapseArrow]")];
    // this.setState({transitions: enable});
    for (let idx=0; idx<components.length; idx++) {
      let component = components[idx];
      if (enable) {
        try {
          component.classList.remove('notransition');
        } catch(e) {}
      } else {
        component.classList.add('notransition'); // Disable transitions
      }
      // component.offsetHeight; // Trigger a reflow, flushing the CSS changes
    }
  };

  updateZipLink = (uri) => {
    this.setState({zipLink: uri, batchURI: uri});
  };

  downloadAll = async () => {

    // Check if there is already a current batch record available
    // let URI = this.state.batchURI;
    // if (URI !== "") {
    //   console.log("Batch still available for download.");
    //   let oDate = new Date();
    //   window.open(URI+"&ignore="+oDate);
    //   this.setState({downloadOpen: true});
    //   return;
    // }

    // Lookup credentials
    let sessionID = localStorage.getItem('sessionID') || "";
    let accessKey = localStorage.getItem('accessKey') || "";

    // Prepare list of desired reports
    let snList = [];
    let reportIdList = [];
    for (let x=0; x<this.state.uploads.length; x++) {
      let upload = this.state.uploads[x];
      if (upload.status === FileStatus.COMPLETE) {
        snList.push(upload.sn);
        reportIdList.push(upload.reportID);
      }
    }

    // Request a new batch download
    let result = null;
    try {
      let requestDT = Math.round(tzCorrect(new Date()).getTime() / 1000);
      const { data } = await this.props.client.query({
        query: BATCH_REQUEST,
        variables: { sessionID, accessKey, snList, reportIdList, requestDT },
        fetchPolicy:'network-only'
      });
      result = data;
    } catch (error) {
      console.dir(error);
      console.log("Error: Unable to complete batch request.");
    }
    if ((result === null) || (result.batchRequest === null)) {
      console.log("failed");
      return;
    }

    // Store batch ID, open dialog, and start polling status
    let batchID = result.batchRequest;
    console.log("Start polling batch: " + batchID);
    this.setState({batchID: batchID, downloadOpen: true});
  };

  // Clear queue
  clearQueue = () => {

    // Clear report queue in database
    let snList = [];
    let reportIdList = [];
    let statusList = [];
    for (let upload of this.state.uploads) {
      if ([FileStatus.QUEUED].includes(upload.status)) {
        snList.push(upload.sn);
        reportIdList.push(upload.reportID);
        statusList.push(upload.status);
      }
    }
    if (snList.length > 0) {
      let sessionID = localStorage.getItem('sessionID') || "";
      let accessKey = localStorage.getItem('accessKey') || "";
      this.props.client.mutate({
        mutation: SET_STATUS,
        variables: { sessionID, accessKey, snList, reportIdList, statusList }
      }).catch (error => {
        console.dir(error);
        console.log("Error: Unable to update report status to error.");
      })
    }

    // Clear uploads
    let uploads = [];
    this.uploadStatusQueue = {};
    this.setState({ uploads, do_poll: false });

    // Clear browser storage
    localStorage.setItem('snList', '[]');
    localStorage.setItem('reportIdList', '[]');
    localStorage.setItem('fileNameList', '[]');
  };

  // Clear batch ID
  clearBatchID = () => {
    console.log("abort batchID");
    this.setState({batchID: null, batchURI: ""})
  };

  // Close options dialog
  closeOptions = () => {
    this.setState({ optionsOpen: false, reportOptions: this.state.defaultOptions, batchID: null, batchURI: ""}, () => {
      this.beginUpload();
    });

    // diagnostic
    setTimeout((error) => {
      console.dir(this.state.uploads);
      console.dir(this.selectedFiles);
    }, UPLOAD_TIMEOUT_RETRY_DELAY * 1000)
  };

  // Open email dialog
  openEmail = async (records) => {

    // Filter files
    let emailRecords = [];
    for (let file of records) {
      if (file.status === FileStatus.COMPLETE)
        emailRecords.push(file);
    }

    // No valid files, do nothing
    if (emailRecords.length === 0)
      return;

    // Prepare filename
    let now = new Date(Date.now());
    if (records.length === 1)
      now = records[0].export;
    let M = "0" + (now.getMonth() + 1);
    M = M.substr(M.length-2);
    let D = "0" + now.getDate();
    D = D.substr(D.length-2);
    let h = "0" + now.getHours();
    h = h.substr(h.length-2);
    let m = "0" + now.getMinutes();
    m = m.substr(m.length-2);
    let emailFileName = "";
    if (records.length === 1) {
      let sn = records[0].sn;
      emailFileName = "VOCSN Multi-View Reports " + now.getFullYear() + "-" + M + "-" + D + " " + h + "-" + m + " - " + sn + ".pdf";
    } else {
      emailFileName = "VOCSN Multi-View Report " + now.getFullYear() + "-" + M + "-" + D + " " + h + "-" + m + ".zip";
    }
    const parts = emailFileName.split('.');
    let emailInputFileName = parts[0];
    let emailInputFileType = parts[1];

    // Single file, no ZIP link needed
    let batchID = this.state.batchID;
    if (emailRecords.length === 1) {
      let emailRecordID = records[0].reportID;
      let emailRecordSN = records[0].sn;
      this.setState({emailOpen: true, emailFiles: emailRecords, emailFileName, emailRecordID, emailRecordSN,
        emailInputFileName, emailInputFileType, zipLink: records[0].uri});

    // Multiple files, make sure ZIP link is available
    } else {

      // Link is not available
      let URI = this.state.batchURI;
      if (URI === "") {

        // Lookup credentials
        let sessionID = localStorage.getItem('sessionID') || "";
        let accessKey = localStorage.getItem('accessKey') || "";

        // Prepare list of desired reports
        let snList = [];
        let reportIdList = [];
        for (let x = 0; x < this.state.uploads.length; x++) {
          let upload = this.state.uploads[x];
          if (upload.status === FileStatus.COMPLETE) {
            snList.push(upload.sn);
            reportIdList.push(upload.reportID);
          }
        }

        // Request a new batch download
        let result = null;
        try {
          let requestDT = Math.round(tzCorrect(new Date()).getTime() / 1000);
          const {data} = await this.props.client.query({
            query: BATCH_REQUEST,
            variables: {sessionID, accessKey, snList, reportIdList, requestDT},
            fetchPolicy: 'network-only'
          });
          result = data;
        } catch (error) {
          console.dir(error);
          console.log("Error: Unable to complete batch request.");
        }
        if ((result === null) || (result.batchRequest === null)) {
          console.log("Error: Zip file creation failed");
          return;
        }

        // Store batch ID, open dialog, and start polling status
        batchID = result.batchRequest;
      }

      // Update link and open window
      let emailRecordID = batchID;
      this.setState({batchURI: URI, batchID, emailOpen: true, emailFiles: emailRecords, emailFileName,
        emailRecordID, emailRecordSN: null, emailInputFileName, emailInputFileType, zipLink: URI});
    }
  };

  // Close email dialog
  closeEmail = (component) => {
    if (this.state.emailFiles.length > 1)
      this.setState({ emailOpen: false, batchURI: component.state.zipLink });
    else
      this.setState({ emailOpen: false});
  };

  // Close download dialog
  closeDownload = (component) => {
    if (component.state.status === FileStatus.ERROR) {
      this.setState({downloadOpen: false, batchID: null, batchURI: ""});
    } else {
      this.setState({downloadOpen: false, batchID: component.state.batchID, batchURI: component.state.batchURI});
    }
  };

  // Label text change
  labelChange = (event) => {
    let target = event.target;
    let id_parts = target.id.split('-');
    let idx = id_parts[id_parts.length-1];
    let upload = this.state.uploads[idx];
    upload.label = target.value;
    this.setState(updateUpload(upload));
  };

  render() {
    const { classes } = this.props;
    const inputFile = createRef(null);
    const pad = null;

    return (
      <div>
        { !isMobile &&
          <div className={classes.blueBar} />
        }
        <div className={classes.content}>
          { ( (!isMobile && (isChrome || isFirefox || isSafari || isOpera || isEdge || isIE )) &&
            <div>
              <div className={classes.uploadPane} />
              <div className={classes.uploadLanding}>
                <Dropzone onDrop={(acceptedFiles, target=this) => { if (isIE) { return; } this.handleDropList(acceptedFiles)} } accept='.tar'
                          noClick noKeyboard>
                  {({getRootProps, getInputProps}) => (
                    <div {...getRootProps()}>
                      <input {...getInputProps()} />
                      <Grid container className={isIE ? classes.noIEFlex : ''}>
                        <Grid item xs={12} style={{textAlign: "center", marginBottom: '12px'}}>
                          <span className={classNames(classes.mainTitle)} >
                            <b>Upload VOCSN Multi-View Data</b>
                          </span>
                        </Grid>
                        <Grid item xs={1}/>
                          { (isIE &&
                            <Grid item xs={12} sm={4}>
                              <Grid container direction="column" className={isIE ? classes.noIEFlex : ''}>
                                <Grid item xs={12} className={classNames(classes.dropGrid)}>
                                  <Typography className={classNames(classes.instructions)} variant='body1'
                                              style={{maxWidth: '300px'}} paragraph>
                                    To upload folders, use:
                                  </Typography>
                                  <BrowserList/>
                                </Grid>
                              </Grid>
                            </Grid>
                          ) || (
                            <Grid item xs={12} sm={4}>
                              <Grid container direction="column" className={isIE ? classes.noIEFlex : ''}>
                                <Grid item xs={12} className={classNames(classes.dropGrid, classes.fixedHeightGrid)}>
                                  <img src="/image/orange_drag.png" alt="Drag and Drop the VOCSN Folder Here"
                                       className={classes.dragImg}/>
                                </Grid>
                                <Grid item xs={12} className={classNames(classes.dropGrid)}>
                                  <Typography className={classNames(classes.instructions)} variant='body1'
                                              paragraph>
                                    Drop "Multi-View_Exports" folder here to instantly upload data
                                  </Typography>
                                </Grid>
                              </Grid>
                            </Grid>
                          )}
                          <Grid item xs={12} sm={2} className={classNames(classes.dropGrid)}>
                            <Typography className={classNames(classes.instructions, classes.orInst)} variant='body1'
                                        paragraph>
                              OR
                            </Typography>
                          </Grid>
                          <Grid item xs={12} sm={4}>
                            <Grid container direction="column" className={isIE ? classes.noIEFlex : ''}>
                              <Grid item xs={12} className={classNames(classes.dropGrid, classes.fixedHeightGrid)}>
                                <input type='file' id='file' style={{display: 'none'}} ref={inputFile} accept=".tar"
                                       multiple onChange={(props) =>
                                    (this.handleDropList(props.target.files))}
                                />
                                <Button className={classNames(classes.orangeButton, classes.browse)} tabIndex={-1}
                                        onClick={() => (this.handleBrowse())}>
                                  Browse
                                </Button>
                              </Grid>
                              <Grid item xs={12} className={classNames(classes.dropGrid)}>
                                <Typography className={classNames(classes.instructions)} variant='body1'
                                            style={{maxWidth: '300px'}} paragraph>
                                  Browse to select files from computer or USB
                                </Typography>
                              </Grid>
                            </Grid>
                          </Grid>
                        <Grid item xs={1}/>
                      </Grid>
                    </div>
                  )}
                </Dropzone>
              </div>
              <div className={classes.uploadTable}>
                <div className={classes.aboveTable}>
                  <div style={{float: 'left'}}>
                    {/*<Button className={classNames(classes.orangeButton, classes.medSmallButton, classes.clearQueueButton)}*/}
                    {/*        onClick={() => (this.clearQueue())} disabled={this.state.uploads.length === 0}  tabIndex={-1}>*/}
                    {/*  Clear Uploads*/}
                    {/*</Button>*/}
                    <Button className={classNames(classes.viewTab, (this.state.view === ViewStates.SERIAL) ? classes.blueButton : classes.orangeButton)}
                            style={{marginLeft: '20px', clear: 'left'}} onClick={() => (this.sortUploads('serial'))} id="SerTab"
                            disabled={(this.state.uploads.length === 0 || this.state.view === ViewStates.SERIAL)} tabIndex={-1}
                    >
                      Serial
                    </Button>
                    <Button className={classNames(classes.viewTab, (this.state.view === ViewStates.DATE) ? classes.blueButton : classes.orangeButton)}
                            onClick={() => (this.sortUploads('date'))} id="DateTab" tabIndex={-1}
                            disabled={(this.state.uploads.length === 0 || this.state.view === ViewStates.DATE)}
                    >
                      Export Date
                    </Button>
                  </div>
                  {/*<Button className={classNames(classes.orangeButton, classes.midButton, classes.uploadButton)} tabIndex={-1}*/}
                  {/*        onClick={() => (this.beginUpload())} disabled={this.state.uploads.filter(x => x.status === FileStatus.EDITING).length === 0}>*/}
                  {/*  Upload Files*/}
                  {/*</Button>*/}
                  <Button className={classNames(classes.orangeButton, classes.midButton, classes.uploadButton)} tabIndex={-1}
                          onClick={() => (this.clearQueue())} disabled={this.state.uploads.length === 0}>
                    Clear Uploads
                  </Button>
                  <Typography className={classNames(classes.mainTitle, classes.tableTitle)} >
                    Uploads
                  </Typography>
                </div>
                <Table className={classes.table}>
                  <TableHead>
                    <TableRow className={classes.tableHeader}>
                      <TableCell padding={pad} className={classes.tableHeadCell} style={{padding: '0px'}}> </TableCell>
                      <TableCell padding={pad} className={classes.tableHeadCell}>
                        {(this.state.view === ViewStates.SERIAL && "Serial") ||
                        (this.state.view === ViewStates.DATE && "Export Date")}
                      </TableCell>
                      <TableCell padding={pad} className={classes.tableHeadCell}>
                        {(this.state.view === ViewStates.SERIAL && "Export Date") ||
                        (this.state.view === ViewStates.DATE && "Serial")}
                      </TableCell>
                      {/*<TableCell padding={pad} className={classes.tableHeadCell} style={{width:'12%'}}>Label</TableCell>*/}
                      <TableCell padding={pad} className={classes.tableHeadCell}>Period</TableCell>
                      <TableCell padding={pad} className={classes.tableHeadCell} style={{width:'25%'}}>Date Range</TableCell>
                      <TableCell padding={pad} className={classes.tableHeadCell} style={{width:'15%'}}>
                        <span>Status</span>
                        { (this.state.uploads.filter(x => x.status === FileStatus.COMPLETE && x.errorLevel === ErrorLevel.ADVISORY).length > 0) &&
                          <React.Fragment>
                            <br/>
                            <img src="/image/warn.png" alt="Advisory" className={classes.warnImg}/>
                            <span className={classes.warnText}>Partial Data</span>
                          </React.Fragment>
                        }
                      </TableCell>
                      <TableCell padding={pad} className={classNames(classes.tableHeadCell)} style={{maxWidth: '100px', width: '15%'}}>
                        <p className={classes.topHeader}>Download</p>
                        {this.state.uploads.filter(x => x.uri !== "").length > 1 &&
                        <Button className={classNames(classes.orangeButton, classes.smallButton)} tabIndex={-1}
                                disabled={this.state.uploads.length === 0 ||
                                (this.state.uploads.filter(x => (FileStatus.ERROR < x.status) && (x.status < FileStatus.COMPLETE)).length > 0)}
                                onClick={this.downloadAll}>
                          <span className={classes.medUpOnly}>Download All</span>
                          <span className={classes.smlDnOnly}>All</span>
                        </Button>
                        }
                      </TableCell>
                      <TableCell padding={pad} className={classNames(classes.tableHeadCell)} style={{maxWidth: '60px', width: '12%'}}>
                        <p className={classes.topHeader}>Email</p>
                        {this.state.uploads.filter(x => x.uri !== "").length > 1 &&
                        <Button className={classNames(classes.orangeButton, classes.smallButton)} tabIndex={-1}
                                disabled={this.state.uploads.length === 0 ||
                                (this.state.uploads.filter(x => (FileStatus.ERROR < x.status) && (x.status < FileStatus.COMPLETE)).length > 0)}
                                onClick={() => this.openEmail(this.state.uploads)}>
                          <span className={classes.medUpOnly}>Email All</span>
                          <span className={classes.smlDnOnly}>All</span>
                        </Button>
                        }
                      </TableCell>
                    </TableRow>
                  </TableHead>
                  {this.state.uploads.length === 0 &&
                  <React.Fragment>
                    <TableBody>
                      <TableRow>
                        <td colSpan='9' className={classes.noUploads}>
                        <span>
                          {'No Files selected to upload.'}
                        </span>
                        </td>
                      </TableRow>
                    </TableBody>
                  </React.Fragment>
                  }
                  <React.Fragment>
                    <TableBody>
                      {this.state.uploads.map((n, idx) => (
                        <TableRow id={("row_" + n.source)} key={"row_" + n.source} className={classes.autoHeight}
                                  style={{background: idx % 2 > 0 ? '#efeff0' : null}}>
                          <CollapsibleCell classNames={classNames(classes.arrowCell)} states={this.state} idx={idx}
                                           upload={n} left fileCount style={{paddingTop: '6px'}}>
                            {this.isSingle(idx) &&
                            <React.Fragment>

                              <ExpandMoreIcon className={classes.collapseArrow} style={this.state.groupExpansion[
                                  (this.state.sortBy === "date") ? n.export : n.sn] ? { transform: 'rotate(0deg)' } : { transform: 'rotate(-90deg)' }}
                                              onClick={(this.isFirstInGroup(idx) && this.isSingle(idx)) ? (() => this.setVisibility(n)) : null}/>
                            </React.Fragment>
                            }
                          </CollapsibleCell>
                          <CollapsibleCell states={this.state} idx={idx} upload={n} refCell style={{verticalAlign: 'top'}}>
                            <b>
                              {(this.state.view === ViewStates.SERIAL && n.sn) ||
                              (this.state.view === ViewStates.DATE && getDateStr(n.export))}
                            </b>
                          </CollapsibleCell>
                          <CollapsibleCell states={this.state} idx={idx} upload={n}>
                            {(this.state.view === ViewStates.SERIAL && getDateStr(n.export)) ||
                            (this.state.view === ViewStates.DATE && n.sn)}
                          </CollapsibleCell>
                          {/*<CollapsibleCell states={this.state} idx={idx} upload={n}>*/}
                          {/*  { (n.status === FileStatus.EDITING &&*/}
                          {/*      <form autoComplete="off">*/}
                          {/*        <TextField*/}
                          {/*            id={'file-label-' + idx}*/}
                          {/*            idx={idx}*/}
                          {/*            value={this.state.uploads[idx].label}*/}
                          {/*            onChange={this.labelChange}*/}
                          {/*            className={classNames(classes.selectBorder, classes.inputText)}*/}
                          {/*            style={{width: '70%'}}*/}
                          {/*        />*/}
                          {/*      </form>*/}
                          {/*  ) ||*/}
                          {/*  n.label*/}
                          {/*  }*/}
                          {/*</CollapsibleCell>*/}
                          <CollapsibleCell states={this.state} idx={idx} upload={n}>{n.period.shortLabel}</CollapsibleCell>
                          <CollapsibleCell states={this.state} idx={idx} upload={n}>{getRange(n.start, n.end)}</CollapsibleCell>
                          <CollapsibleCell states={this.state} idx={idx} upload={n} style={{padding: '0'}}>
                            { (n.status === FileStatus.COMPLETE) && (n.errorLevel === ErrorLevel.ADVISORY) &&
                                <img src="/image/warn.png" alt="Advisory" className={classes.warnImg} style={{position: 'relative', top: '2px'}}/> }
                            <span className={classes.status}>{PROCESSING_STATUS.find(x => x.code === parseInt(n.status, 10)).label}</span>
                            { (n.status === FileStatus.UPLOADING) && <LinearProgress variant="determinate" value={100 * n.progress} style={{width: '90%', margin: 'auto'}}/> }
                            { (n.status === FileStatus.QUEUED) && <DisabledProgress variant="determinate" value={0} style={{width: '90%', margin: 'auto'}}/> }
                            { (n.status === FileStatus.PROCESSING) && <ProcessingProgress variant="query" style={{width: '90%', margin: 'auto'}}/> }
                            { (n.status === FileStatus.COMPLETE) && <LinearProgress variant="determinate" value={100} color="secondary" style={{width: '90%', margin: 'auto'}}/> }
                            { (n.status === FileStatus.ERROR) && <ErrorProgress variant="determinate" value={100} style={{width: '90%', margin: 'auto'}}/> }
                            { (n.status === FileStatus.RETRYING) && <DisabledProgress variant="determinate" value={0} style={{width: '90%', margin: 'auto'}}/> }
                          </CollapsibleCell>
                          <CollapsibleCell states={this.state} idx={idx} upload={n}>
                            {((n.status !== FileStatus.COMPLETE) && (n.uri !== null)) ? "---" :
                                <a href={n.uri} tabIndex='-1' download>
                                  <Button tabIndex={-1}>
                                    <img src="/image/pdf.png" alt="Download Report" className={classes.downloadImg}/>
                                  </Button>
                                </a>
                            }
                          </CollapsibleCell>
                          <CollapsibleCell states={this.state} idx={idx} upload={n}>
                            {((n.status !== FileStatus.COMPLETE) && (n.uri !== null)) ? "---" :
                                <Button onClick={() => {this.openEmail([n])}} tabIndex={-1}>
                                  <img src="/image/email.png" alt="Email Report" className={classes.emailImg} />
                                </Button>
                            }
                          </CollapsibleCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </React.Fragment>
                </Table>
                <ReportStatus component={this} snList={this.state.uploads.filter(a => { return ((a.status === 3) || (a.status === 4)) }).map(a => a.sn.toString())}
                              reportIdList={this.state.uploads.filter(a => { return ((a.status === 3) || (a.status === 4)) }).map(a => a.reportID)} do_poll={this.state.do_poll} />
              </div>
            </div>
          ) || (
            <div>
              <div style={{width: '100%'}}>
                <Typography className={classNames(classes.instructions)} variant='body1'
                            style={{maxWidth: '400px', textAlign: 'center', marginTop: '20px'}} paragraph>
                  Please view VOCSN Multi-View Reports
                </Typography>
                <Typography className={classNames(classes.instructions)} variant='body1'
                            style={{maxWidth: '400px', textAlign: 'center', marginBottom: '10px'}} paragraph>
                  using a supported desktop browser.
                </Typography>
                <BrowserList/>
              </div>
            </div>
          ) }

        </div>

        <div id="message-box" className={classes.messageBox}/>

        <ReportOptionsDialog reportOptions={this.state.activeOptions} selectedFiles={this.getSelectedFiles}
                             open={this.state.optionsOpen} onClose={this.closeOptions}
                             onAccept={(options) => this.updateOptions(options)}/>
        <EmailOptionsDialog sendFiles={this.state.emailFiles} open={this.state.emailOpen} onClose={this.closeEmail}
                            client={this.props.client} fileName={this.state.emailFileName}
                            inputFileName={this.state.emailInputFileName} inputFileType={this.state.emailInputFileType}
                            zipLink={this.state.zipLink} abort={this.clearBatchID} batchID={this.state.batchID}
                            recordID={this.state.emailRecordID} gotLink={this.updateZipLink}
                            sn={this.state.emailRecordSN}/>
        <DownloadDialog batchID={this.state.batchID} open={this.state.downloadOpen} onClose={this.closeDownload}
                        sessionID={localStorage.getItem('sessionID') || ""} sAccessKey={localStorage.getItem('accessKey') || ""}
                        abort={this.clearBatchID} batchURI={this.state.batchURI}/>
      </div>
    );
  }
}

export default withStyles(styles, { withTheme: true })(withApollo(GuestUpload));
