/**
 * Responsive dialog to display batch download status.
 */
import React from 'react';
import classNames from 'classnames';
import { Query } from 'react-apollo';
import Grid from '@material-ui/core/Grid';
import Paper from '@material-ui/core/Paper';
import Button from '@material-ui/core/Button';
import { withStyles } from '@material-ui/core/styles';
import { Dialog, DialogContent, LinearProgress } from '@material-ui/core';

import { BATCH_DOWNLOAD } from '../data/queries';
import {FileStatus, themePalette,} from '../data/ui_constants';

const styles = theme => ({
  formContainer: {
    display: 'flex',
    flexWrap: 'wrap',
    // backgroundColor: 'plum', // ;;;;;;;;;;;
  },
  paper: {
    paddingLeft: theme.spacing() * 2,
    paddingRight: theme.spacing() * 2,
    boxShadow: 'none',
    color: theme.palette.text.secondary,
  },
  blueBorder: {
    '& > div:nth-child(3)': {
      '& > div': {
        borderRadius: '20px',
        border: '7px',
        borderStyle: 'solid',
        borderColor: theme.palette.primary.main,
        width: 'calc(200px + 30%)',
        maxWidth: 'none',
        boxShadow: 'none'
      }
    },
    '& > div.MuiBackdrop-root': {
      backgroundColor: 'rgb(0, 0, 0, 0.2)',
    }
  },
  progressBar: {
    width: '80%',
    margin: 'auto'
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
  downloadDiv: {
    width: '85%',
    margin: 'auto',
    padding: '8px 0px',
  },
  label: {
    lineHeight: '40px',
    transform: 'none',
    paddingRight: '10px',
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
    fontStyle: 'italic',
    fontSize: '10px',
    [theme.breakpoints.up('md')]: {
      fontSize: '14px'
    },
    [theme.breakpoints.up('lg')]: {
      fontSize: '16px'
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
        backgroundColor: theme.palette.ternary.main,
      },
    },
    '&:disabled': {
      color: theme.palette.disabled.light,
      backgroundColor: theme.palette.disabled.dark,
    }
  },
});

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

// Poll the database and check for report status updates
const DownloadStatus = ({ component, batchID, doPoll }) => (
    <Query
        query={BATCH_DOWNLOAD}
        variables={{
          sessionID: component.props.sessionID,
          accessKey: component.props.sAccessKey,
          batchID
        }}
        skip={doPoll !== true}
        pollInterval={ doPoll ? 500 : 0 }
    >
      {({ data }) => {

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
                  console.log("Report batch ready for download.");
                  component.setState({batchURI: URI, status, progress, message });
                  window.location = URI;
                } else {
                  if (component.props.abort)
                    component.props.abort();
                  component.setState({batchID: null, batchURI: URI, status, progress, message });
                }

              // Update progress
              } else {
                if ((progress !== component.state.progress) || (status !== component.state.status))
                  component.setState({progress, status, message});
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

class DownloadDialog extends React.Component {
  state = {
    dirty: false,
    batchID: this.props.batchID,
    batchURI: "",
    status: FileStatus.QUEUED,
    progress: 0,
  };

  // getDerivedStateFromProps
  // Initialize the state variables with the next property object
  // NOTE: Invoked before a mounted component receives new props. To update state in response to prop changes (e.g. to
  // reset it), you may compare this.props & nextProps, and perform state transitions using setState() in this method.
  static getDerivedStateFromProps(nextProps, state) {
    const { batchID, batchURI, open } = nextProps;
    if ((open !== state.open) || (batchID !== state.batchID)) {
      return {
        batchID,
        batchURI,
        open,
      };
    }
    return null;
  }

  handleClose = () => {
    this.props.onClose(this);
  };

  render() {
    const { classes, open } = this.props;

    return (
      <Dialog
        open={open}
        onClose={this.handleClose}
        aria-labelledby='download-dialog'
        className={classes.blueBorder}
      >
        <DialogContent className={classes.downloadDiv}>
          <form className={classes.formContainer}>
            <Grid container style={{marginBottom: '0px'}}>

              {/* Report Section Selection */}
              <Grid item xs={12} style={{width: '100%'}}>
                <Paper className={classes.paper}>
                  <div className={classNames(classes.mainTitle, classes.doubleSpaceBelow, classes.center)}>
                    Batch Download
                  </div>

                </Paper>
              </Grid>
            </Grid>

            <Grid container style={{marginBottom: '0px'}}>
              <Grid item xs={12} style={{width: '100%'}}>
                <Paper className={classes.paper}>
                  <div style={{textAlign: 'center'}}>
                    <span className={classes.label} style={{padding: '0px'}}>
                      { ((this.state.status === FileStatus.COMPLETE || this.state.batchURI !== "") && "Files Ready") ||
                        ((this.state.status === FileStatus.ERROR) && "Error") || "Preparing Files"}
                    </span>
                  </div>
                  <div className={classes.progressBar}>
                    {
                      ((this.state.status === FileStatus.COMPLETE || this.state.batchURI !== "") && <LinearProgress variant="determinate" value={100} color="secondary"/>) ||
                      ((this.state.status === FileStatus.QUEUED) && <DisabledProgress variant="determinate" value={0}/>) ||
                      ((this.state.status === FileStatus.PROCESSING) && <LinearProgress variant="determinate" value={100 * this.state.progress}/>) ||
                      ((this.state.status === FileStatus.ERROR) && <ErrorProgress variant="determinate" value={100}/>)
                    }
                  </div>

                </Paper>
              </Grid>
            </Grid>

            <Grid container style={{marginBottom: '0px'}}>
              <Grid item xs={12} style={{width: '100%'}}>
                <Paper className={classes.paper} style={{marginTop: '10px', marginBottom: '25px'}}>
                  <div style={{textAlign: 'center'}}>
                    <span className={classes.smallLabel}>
                      {(this.state.batchURI !== "" &&
                        "Download should start automatically.") || <div>&nbsp;</div>
                      }
                    </span>
                  </div>
                  <div style={{textAlign: 'center'}}>
                    <span className={classes.smallLabel}>
                      {(this.state.batchURI !== "" &&
                          <div id="download">If it doesn't, <a href="#download" onClick={() => {let oDate = new Date(); window.open(this.state.batchURI+"&ignore="+oDate)}}>
                            click here
                          </a> to begin.</div>) || <div>&nbsp;</div>
                      }
                    </span>
                  </div>

                </Paper>
              </Grid>
            </Grid>

            <Grid container style={{marginBottom: '0px'}}>
              <Grid item xs={12} style={{width: '100%'}}>
                <Paper className={classes.paper}>
                  <div  style={{textAlign: 'center', marginBottom: '20px'}}>
                    <Button className={classNames(classes.orangeButton, classes.midButton)}
                            onClick={this.handleClose} disabled={false}>
                      Close
                    </Button>
                  </div>
                </Paper>
              </Grid>
            </Grid>

          </form>
        </DialogContent>
        <DownloadStatus component={this} batchID={this.state.batchID}
                        doPoll={this.state.batchID !== null && this.status !== FileStatus.ERROR &&
                        this.state.batchURI === "" && this.state.open} />
      </Dialog>
    );
  }
}

// NOTE: Use 'withStyles' when you want to provide styles through the Material-UI 'classes' object.
export default (withStyles(styles, { withTheme: true })(DownloadDialog));
