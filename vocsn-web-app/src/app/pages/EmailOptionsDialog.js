/**
 * Responsive dialog to setup email delivery.
 */
import React from 'react';
import { Query } from 'react-apollo';
import Button from '@material-ui/core/Button';
import TextField from '@material-ui/core/TextField';
import Grid from '@material-ui/core/Grid';
import Paper from '@material-ui/core/Paper';
import {
  FormControl,
  Dialog,
  DialogContent,
  withMobileDialog,
  LinearProgress
} from '@material-ui/core';
import classNames from 'classnames';
import InputLabel from '@material-ui/core/InputLabel';
import { withStyles } from '@material-ui/core/styles';

import {
  getStart,
  FileStatus, themePalette,
} from '../data/ui_constants';
import {BATCH_DOWNLOAD, SEND_EMAIL} from "../data/queries";

const styles = theme => ({
  formContainer: {
    display: 'flex',
    flexWrap: 'wrap',
    // backgroundColor: 'plum', // ;;;;;;;;;;;
  },
  paper: {
    paddingLeft: theme.spacing() * 2,
    paddingRight: theme.spacing() * 2,
    // paddingLeft: 16,
    // paddingRight: 16,
    // textAlign: 'center',
    boxShadow: 'none',
    color: theme.palette.text.secondary,
    // backgroundColor: 'aqua', //;;;;;;;;;
  },
  blueBorder: {
    '& > div:nth-child(3)': {
      '& > div': {
        borderRadius: '20px',
        border: '7px',
        borderStyle: 'solid',
        borderColor: theme.palette.primary.main,
        width: 'calc(460px + 30%)',
        maxWidth: 'none',
        boxShadow: 'none'
      }
    },
    '& > div.MuiBackdrop-root': {
      backgroundColor: 'rgb(0, 0, 0, 0.2)',
    }
  },
  noBorder: {
    '& div:nth-child(2)': {
      border: 'none'
    }
  },
  formGroup: {
    display: 'block',
  },
  formItem: {
    width: '100%',
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
  normalText: {
    '& span': {
      fontSize: '15px',
      fontFamily: '"avenir-roman","Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif',
      [theme.breakpoints.up('sm')]: {
        fontSize: '18px',
      },
      [theme.breakpoints.up('md')]: {
        fontSize: '21px'
      },
      [theme.breakpoints.up('lg')]: {
        fontSize: '24px'
      }
    }
  },
  inputText: {
    '& div': {
      '& input': {
        fontSize: '16px',
        fontFamily: '"avenir-roman","Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif',
        [theme.breakpoints.up('sm')]: {
          fontSize: '18px',
        },
        [theme.breakpoints.up('md')]: {
          fontSize: '20px'
        },
        [theme.breakpoints.up('lg')]: {
          fontSize: '22px'
        },
      }
    }
  },
  title: {
    margin: theme.spacing(),
    textAlign: 'center',
  },
  center: {
    textAlign: 'center',
  },
  spaceBelow: {
    marginBottom: '10px',
  },
  doubleSpaceBelow: {
    marginBottom: '20px',
  },
  formControl: {
    width: 'calc(100% - 25px)',
    minWidth: 120,
  },
  emailDiv: {
    width: '85%',
    margin: 'auto',
    minWidth: '420px',
    padding: '8px 0px',
  },
  label: {
    lineHeight: '40px',
    transform: 'none',
    padding: '3px 10px 0 0',
    position: 'static',
    fontSize: '16px',
    fontFamily: '"avenir-roman","Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif',
    [theme.breakpoints.up('sm')]: {
      fontSize: '18px',
    },
    [theme.breakpoints.up('md')]: {
      fontSize: '22px'
    },
    [theme.breakpoints.up('lg')]: {
      fontSize: '24px'
    }
  },
  smallLabel: {
    fontSize: '14px',
    [theme.breakpoints.up('md')]: {
      fontSize: '20px'
    },
    [theme.breakpoints.up('lg')]: {
      fontSize: '22px'
    }
  },
  labelRight: {
    width: '90%',
    textAlign: 'right',
    marginRight: '10px'
  },
  selectBorder: {
    width: '100%',
    margin: '0px',
    borderRadius: 25,
    position: 'relative',
    backgroundColor: theme.palette.background.paper,
    border: '2px solid #a8a9ad',
    padding: '3px 0px 3px 13px',
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
        fontSize: '14px',
        paddingBottom: '0px',
        fontFamily: '"avenir-roman","Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif',
        [theme.breakpoints.up('sm')]: {
          fontSize: '15px',
        },
        [theme.breakpoints.up('lg')]: {
          fontSize: '16px'
        },
        [theme.breakpoints.up('xl')]: {
          fontSize: '18px'
        },
        '&:focus': {
          borderColor: 'white',
        },
      },
      '& input': {
        width: '97%'
      }
    }
  },
  datePick: {
    '& > div': {
      '& > input': {
        width: '250%'
      }
    }
  },
  textField: {
    margin: theme.spacing(),
    // marginLeft: theme.spacing(),
    // marginRight: theme.spacing(),
    minWidth: 120,
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
        backgroundColor: theme.palette.ternary.main,
      },
    },
    '&:disabled': {
      color: theme.palette.disabled.light,
      backgroundColor: theme.palette.disabled.dark,
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
  alignCell: {
    padding: '0px',
    border: 'none',
    width: '55px'
  },
  shrink: {
    transformOrigin: 'top left',
    transform: 'translate(0, 1.5px) scale(0.75)'
  },
  moveDown: {
    marginTop: '16px'
  }
});

const TAG = 'EmailOptionsDialog:';

const EmailStatus = {
  ERROR: -1,
  EDITING: 0,
  SENDING: 1,
  COMPLETE: 2
};

// Poll the database and check for report status updates
const DownloadStatus = ({ component, batchID, doPoll }) => (
    <Query
        query={BATCH_DOWNLOAD}
        variables={{
          sessionID: localStorage.getItem('sessionID') || "",
          accessKey: localStorage.getItem('accessKey') || "",
          batchID
        }}
        skip={doPoll !== true}
        pollInterval={ doPoll ? 500 : 0 }
    >
      {({ data }) => {

        // Throttle
        console.log("check download");
        console.log(batchID);
        let now = Date.now();
        if (now - component.lastPoll < 500)
          return <div/>;
        component.lastPoll = now;

        // Catch errors
        try {

          // Read data
          if (data !== undefined) {
            let result = data.batchDownload;
            if (result !== undefined) {
              let status = result.status;
              let progress = result.progress;
              let URI = result.URI;
              let message = result.message;

              // Batch complete and link available or encountered error. Stop.
              if ((status === FileStatus.ERROR) || (status === FileStatus.COMPLETE && URI !== "")) {
                if (status === FileStatus.COMPLETE && URI !== "") {
                  component.props.gotLink(URI);
                  component.setState({zipLink: URI, zipStatus: status, progress, message });
                } else {
                  if (component.props.abort)
                    component.props.abort();
                  component.setState({batchID: null, zipLink: URI, zipStatus: status, progress, message });
                }

              // Update progress
              } else {
                if ((progress !== component.state.progress) || (status !== component.state.status))
                  component.setState({progress, zipStatus: status, message});
              }
            }
          }

        } catch (err) {
          console.log(err);
        }
        return <div/>;
      }}
    </Query>
);

function emailIsValid (email) {
  return /^\w+([.-]?\w+)*@\w+([.-]?\w+)*(\.\w{2,3})+$/.test(email);
}

// Request report list from server on page reload
const sendEmail = async (page) => {

  // Lookup report list for upload page
  let sessionID = localStorage.getItem('sessionID') || "";
  let accessKey = localStorage.getItem('accessKey') || "";

  // Prepare email arguments
  let recordID = page.state.recordID;
  let sn = page.state.recordSN;
  let fromName = page.state.email_from;
  let subject = page.state.email_subject;
  let toAddress = page.state.email_to;
  let link = page.state.zipLink;
  let fileName = page.state.filename;
  let sendDate = Math.round(Date.now() / 1000);
  let multiple = page.state.files.length > 1;
  console.log("send email:", recordID);

  // Validate inputs
  if ((recordID === null) || (recordID === "") ||
      (fromName === null) || (fromName === "") ||
      (toAddress === null) || (toAddress === "") ||
      (subject === null) || (subject === "") ||
      (fileName === null) || (fileName === "")) {
    alert("Please complete the email form.");
    return;
  }

  let useMultiEmail = true;

  // Check single email
  if (!useMultiEmail) {
    if (!emailIsValid(toAddress)) {
      alert("Please enter a valid email address in the 'To' field.");
      return;
    }
  }


  // Parse email
  else {
    toAddress = toAddress.replace(/[\|;:&]/gi, ',');
    toAddress = toAddress.replace(/\s\s+/gi, ' ');
    toAddress = toAddress.replace(/ ,/gi, ',');
    toAddress = toAddress.replace(/, /gi, ',');
    toAddress = toAddress.replace(/ /gi, ',').split(',');
    for (let email of toAddress) {
      if (!emailIsValid(email)) {
        alert("Please enter a valid email address in the 'To' field.");
        return;
      }
    }
  }

  // Set status
  page.setState({emailStatus: EmailStatus.SENDING});

  // Request details from server
  let result = null;
  try {
    const {data} = await page.props.client.query({
      query: SEND_EMAIL,
      variables: {sessionID, accessKey, recordID, fromName, subject, toAddress, link, fileName, sendDate, multiple, sn}
    });
    result = data.sendEmail;
    console.dir(result);
    if (result === null) {
      console.log("Error: failed to send email.");
      page.setState({emailStatus: EmailStatus.ERROR});
    } else {
      console.log("Successfully sent email.");
      page.setState({emailStatus: EmailStatus.COMPLETE, sent: true});
    }

  } catch (error) {
    console.dir(error);
    console.log("Error: Encountered error while sending email.");
    page.setState({emailStatus: EmailStatus.ERROR});
  }

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

const ErrorProgress = withStyles({
  colorPrimary: {
    backgroundColor: themePalette.palette.error.main,
  },
  barColorPrimary: {
    backgroundColor: themePalette.palette.error.main,
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

class EmailOptionsDialog extends React.Component {
  constructor(props) {
    super(props);
    this.lastPoll = Date.now();
  };
  state = {
    dirty: false,
    sent: false,
    email_from: '',
    email_to: '',
    email_subject: 'VOCSN Multi-View Reports',
    emailSN: null,
    batchID: null,
    recordID: null,
    filename: 'VOCSN Multi-View Reports DD-MM-YYYY.zip',
    inputFileName: null,
    inputFileType: null,
    files: [],
    zipStatus: FileStatus.PENDING,
    zipLink: '',
    emailStatus: EmailStatus.EDITING
  };

  // getDerivedStateFromProps
  // Initialize the state variables with the next property object
  // NOTE: Invoked before a mounted component receives new props. To update state in response to prop changes (e.g. to
  // reset it), you may compare this.props & nextProps, and perform state transitions using setState() in this method.
  static getDerivedStateFromProps(nextProps, state) {
    // const { } = nextProps;
    if (nextProps.open !== state.open) {
      let sent = (nextProps.open === true && state.open === false) ? false: state.sent;
      let emailStatus = nextProps.zipLink === "" ? EmailStatus.EDITING : EmailStatus.COMPLETE;
      return{
        dirty: false,
        sent,
        email_from: '',
        email_to: '',
        email_subject: 'VOCSN Multi-View Reports',
        open: nextProps.open,
        batchID: nextProps.batchID,
        recordID: nextProps.recordID,
        recordSN: nextProps.sn,
        inputFileName: nextProps.inputFileName,
        inputFileType: nextProps.inputFileType,
        filename: nextProps.fileName,
        files: nextProps.sendFiles,
        zipLink: nextProps.zipLink,
        zipStatus: FileStatus.PENDING,
        emailStatus
      }
    }
    return null;
  }

  handleChangeFrom = (event) => {
    this.setState({ email_from: event.target.value, dirty: true });
  };

  handleChangeTo = (event) => {
    this.setState({ email_to: event.target.value, dirty: true });
  };

  handleChangeSubject = (event) => {
    this.setState({ email_subject: event.target.value, dirty: true });
  };

  handleChangeFilename = (event) => {
    let name = event.target.value;
    name = name.replace(/[/\\?%*:|"<>]/g, '-');
    const filename = name + "." + this.state.inputFileType;
    this.setState({ inputFileName: name, filename, dirty: true });
  };

  handleChangePeriod = (event) => {
    const per = event.target.value;
    console.log(per);
    this.setState({ period_mine: per, start: getStart(this.state.end, per), dirty: true });
  };

  handleSave = () => {
    this.props.reportOptions.start = this.state.start;
    this.props.reportOptions.end = this.state.end;
    this.props.reportOptions.period = this.state.period_mine;
    this.props.reportOptions.sections = this.state.sections;
    console.log(this.state.period);
    console.log(this.props.reportOptions.period);
    this.props.onClose();
  };

  handleCancel = () => {
    console.log(TAG, 'handleCancel');
    this.props.onClose(this);
  };

  render() {
    const { classes, open } = this.props;

    return (
      <Dialog
        open={open}
        onClose={this.handleCancel}
        aria-labelledby='report-configuration-dialog'
        className={classes.blueBorder}
      >
        <DialogContent className={classes.emailDiv}>
          <form className={classes.formContainer}>
            <Grid container style={{marginBottom: '0px'}}>

              {/* Report Section Selection */}
              <Grid item xs={12} style={{width: '100%'}}>
                <Paper className={classes.paper}>
                  <div className={classNames(classes.mainTitle, classes.doubleSpaceBelow, classes.center)}>
                    Email Multi-View Reports
                  </div>

                  {/* File preparation when required */}
                  <Grid container>
                    <Grid item xs={12} style={{width: '100%'}}>
                      <Paper className={classes.paper}>
                        <div style={{textAlign: 'center'}}>
                          <span className={classes.label}>
                            {
                              (
                                ((this.state.emailStatus === EmailStatus.COMPLETE) && (this.state.sent === true) && "Email Sent") ||
                                ((this.state.emailStatus === EmailStatus.SENDING) && "Sending") ||
                                ((this.state.emailStatus === EmailStatus.ERROR) && "Error - Email not sent")
                              ) || (
                                ((this.state.files.length === 1 &&
                                  "File Ready"
                                ) || (
                                  ((this.state.zipStatus === FileStatus.COMPLETE || this.state.zipLink !== "") && "Files Ready") ||
                                  ((this.state.zipStatus === FileStatus.ERROR) && "Error - File Unavailable") || "Preparing Files"
                                ))
                              )}
                          </span>
                        </div>
                        <div className={classes.progressBar} style={{height: '4px', width: '60%', margin: 'auto', marginBottom: '25px'}}>
                          {
                            (
                              ((this.state.emailStatus === EmailStatus.COMPLETE) &&
                                <LinearProgress variant="determinate" value={100} color="secondary"/>) ||
                              ((this.state.emailStatus === EmailStatus.SENDING) &&
                                <ProcessingProgress variant="query"/>) ||
                              ((this.state.emailStatus === EmailStatus.ERROR) &&
                                <ErrorProgress variant="determinate" value={100}/>)
                            ) || (
                              ((this.state.zipStatus === FileStatus.COMPLETE || this.state.zipLink !== "") &&
                                <LinearProgress variant="determinate" value={100} color="secondary"/>) ||
                              ((this.state.zipStatus === FileStatus.QUEUED) &&
                                <DisabledProgress variant="determinate" value={0}/>) ||
                              ((this.state.zipStatus === FileStatus.PROCESSING) &&
                                <LinearProgress variant="determinate" value={100 * this.state.progress}/>) ||
                              ((this.state.zipStatus === FileStatus.ERROR) &&
                                <ErrorProgress variant="determinate" value={100}/>)
                            )
                          }
                        </div>

                      </Paper>
                    </Grid>
                  </Grid>

                  {/* Email from field */}
                  <FormControl className={classNames(classes.formControl, classes.spaceBelow)}>
                    <Grid container>
                      <Grid item xs={2} className={classes.alignCell}>
                        <div className={classes.labelRight}>
                          <InputLabel className={classNames(classes.formItem, classes.label)}
                                      htmlFor='email-from-id'>From:</InputLabel>
                        </div>
                      </Grid>
                      <Grid item xs={10} className={classes.alignCell} style={{width: '80%'}}>
                        <TextField
                            name='email-from'
                            id='email-from-id'
                            value={this.state.email_from}
                            placeholder='<enter your name and/or organization>'
                            onChange={this.handleChangeFrom}
                            className={classNames(classes.selectBorder, classes.inputText)}
                        />
                      </Grid>
                    </Grid>
                  </FormControl>

                  {/* Email to field */}
                  <FormControl className={classNames(classes.formControl, classes.spaceBelow)}>
                    <Grid container>
                      <Grid item xs={2} className={classes.alignCell}>
                        <div className={classes.labelRight}>
                          <InputLabel className={classNames(classes.formItem, classes.label)}
                                      htmlFor='email-to-id'>To:</InputLabel>
                        </div>
                      </Grid>
                      <Grid item xs={10} className={classes.alignCell} style={{width:'80%'}}>
                        <TextField
                            name='email-to'
                            id='email-to-id'
                            value={this.state.email_to}
                            placeholder='<enter recipient email address>'
                            onChange={this.handleChangeTo}
                            className={classNames(classes.selectBorder, classes.inputText)}
                        />
                      </Grid>
                    </Grid>
                  </FormControl>

                  {/* Email subject */}
                  <FormControl className={classNames(classes.doubleSpaceBelow, classes.formControl)}>
                    <Grid container>
                      <Grid item xs={2} className={classes.alignCell}>
                        <div className={classes.labelRight}>
                          <InputLabel className={classNames(classes.formItem, classes.label)}
                                      htmlFor='email-subject-id'>Subject:</InputLabel>
                        </div>
                      </Grid>
                      <Grid item xs={10} className={classes.alignCell} style={{width:'80%'}}>
                        <TextField
                            name='email-subject'
                            id='email-subject-id'
                            value={this.state.email_subject}
                            placeholder='<enter email subject>'
                            onChange={this.handleChangeSubject}
                            className={classNames(classes.selectBorder, classes.inputText)}
                        />
                      </Grid>
                    </Grid>
                  </FormControl>

                </Paper>
              </Grid>
            </Grid>

            <Grid container style={{marginBottom: '0px'}}>
              <Grid item xs={12} style={{width: '100%'}}>
                <Paper className={classes.paper}>
                  <div style={{textAlign: 'center'}}>
                    <span className={classes.label}>
                      {this.state.files.length} Files Included in Attachment
                    </span>
                  </div>

                  {/* File name */}
                  <FormControl className={classNames(classes.doubleSpaceBelow, classes.formControl)}>
                    <Grid container>
                      <Grid item xs={2} className={classes.alignCell}>
                        <div className={classes.labelRight}>
                          <InputLabel className={classNames(classes.formItem, classes.label, classes.smallLabel)}
                                      htmlFor='filename-id'>Filename:</InputLabel>
                        </div>
                      </Grid>
                      <Grid item xs={10} className={classes.alignCell} style={{width:'80%'}}>
                        <TextField
                            name='filename'
                            id='filename-id'
                            value={this.state.inputFileName}
                            placeholder='<enter file name>'
                            onChange={this.handleChangeFilename}
                            className={classNames(classes.selectBorder, classes.inputText)}
                            style={{width: 'calc(100% - 80px)', float: 'left'}}
                        />
                        <div className={classes.label} style={{float: 'left', padding: '3px 0 0 10px'}}>
                          .{ this.state.inputFileType }
                        </div>
                      </Grid>
                    </Grid>
                  </FormControl>
                </Paper>
              </Grid>
            </Grid>

            <Grid container style={{marginBottom: '0px'}}>
              <Grid item xs={12} style={{width: '100%'}}>
                <Paper className={classes.paper}>
                  <div  style={{textAlign: 'center', marginBottom: '20px'}}>
                    <Button onClick={this.handleCancel} color='primary'>
                      Cancel
                    </Button>
                    {((this.state.emailStatus === EmailStatus.COMPLETE) && (this.state.sent === true) &&
                      <Button className={classNames(classes.orangeButton, classes.midButton)}
                              onClick={this.handleCancel}>
                        Close
                      </Button>
                    ) || (
                      <Button className={classNames(classes.orangeButton, classes.midButton)}
                              onClick={() => sendEmail(this)}
                              disabled={(this.state.files.length > 1 && this.state.zipLink === "") ||
                              (this.state.emailStatus === EmailStatus.SENDING)}>
                        Send Email
                      </Button>
                    )}
                  </div>
                </Paper>
              </Grid>
            </Grid>

          </form>
        </DialogContent>
        <DownloadStatus component={this} batchID={this.state.batchID}
                        doPoll={this.state.zipLink !== null && this.status !== FileStatus.ERROR &&
                        this.state.zipLink === "" && this.state.open && this.state.files.length > 1} />
      </Dialog>
    );
  }
}

// NOTE: Use 'withStyles' when you want to provide styles through the Material-UI 'classes' object.
export default withMobileDialog()(withStyles(styles, { withTheme: true })(EmailOptionsDialog));
