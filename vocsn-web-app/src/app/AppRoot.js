import React, { Component } from 'react';
import { withApollo } from 'react-apollo';
import { withStyles } from '@material-ui/core/styles';
import { BrowserRouter, Route, Switch } from 'react-router-dom';

import { DRAWER_WIDTH, NAV_DEFAULT, NAV_UPLOAD } from './data/ui_constants';
import LoginDialog from './components/LoginDialog';
import InactivityDialog from './components/InactivityDialog';
import UserInactivityTimer from './UserInactivityTimer';
import Viewer from './data/Viewer';
import { GET_SESSION, authenticateViewer } from './data/queries';
import { SYS_VER, MOD_VER, USE_VAL_LANDING } from "./config";

import GuestUpload from "./pages/GuestUpload";
import ValidationLanding from "./pages/ValidationLanding";
import TermsLanding from "./pages/TermsLanding";

const TAG = 'AppRoot:';

const styles = theme => ({
  root: {
    position: 'relative',
    display: 'flex',
    // flexGrow: 1,
    minWidth: '500px',
    width: '100%',
    height: '100%',
    // margin: 'auto',
    // zIndex: 1,
    marginTop: '15px',
    textAlign: 'center',
    [theme.breakpoints.up('md')]: {
      marginTop: '25px',
    },
    [theme.breakpoints.up('lg')]: {
      marginTop: '0px',
    },
  },
  logo: {
    position: 'absolute',
    width: '160px',
    height: '64px',
    left: '20px',
    top: '-20px',
    [theme.breakpoints.up('md')]: {
      width: '190px',
      height: '76px',
      left: '24px',
      top: '-25px',
    },
    [theme.breakpoints.up('lg')]: {
      width: '240px',
      height: '96px',
      left: '30px',
      top: '0px'
    },
    [theme.breakpoints.up('xl')]: {
      width: '280px',
      height: '112px',
      left: 'calc(max(calc(100% - 1470px), 50px) / 2)',
    }
  },
  version: {
    position: 'absolute',
    top: '0',
    right: '0',
    width: '20px',
    height: '20px'
  },
  inactiveDialog: {
    '& > div:nth-child(3)': {
      '& > div': {
        borderRadius: '20px',
        border: '7px',
        borderStyle: 'solid',
        borderColor: theme.palette.primary.main,
        boxShadow: 'none'
      }
    },
    '& > div.MuiBackdrop-root': {
      backgroundColor: 'rgb(0, 0, 0, 0.2)',
    }
  },
  content: {
    // backgroundColor: 'white',
    // overflowX: 'auto', // Adds responsive horizontal scrolling for RoomConfig table, and scrollbar at bottom of table
    // padding: theme.spacing(3),
    padding: '0px',
    // Adjust height/margin to shrink height of AppBar for mobile screen sizes
    // Also subtract page padding (2 * 24) to fill vertical space
    // height: 'calc(100% - 70px)',


    width: '100%',
    margin: '25px auto',
    minWidth: '500px',
    maxWidth: '775px',
    [theme.breakpoints.up('md')]: {
      maxWidth: '1000px',
    },
    [theme.breakpoints.up('lg')]: {
      maxWidth: '1200px',
      marginTop: '70px',
    },
    [theme.breakpoints.up('xl')]: {
      maxWidth: '1500px'
    },

    // marginLeft: 0,
    // zIndex: 1,
    // [theme.breakpoints.up('md')]: {
    //   width: `calc(100% - ${DRAWER_WIDTH}px)`,
    //   marginLeft: DRAWER_WIDTH,
    // },
  },
  grayBar: {
    position: 'absolute',
    top: '25px',
    left: '0px',
    right: '0px',
    height: '380px',
    backgroundImage: 'radial-gradient(100% 100% at center, #E9EAEB, #D0D1D2)',
    zIndex: '-1',
    [theme.breakpoints.up('sm')]: {
      height: '290px',
    },
    [theme.breakpoints.up('lg')]: {
      height: '300px',
      top: '70px'
    },
    [theme.breakpoints.up('xl')]: {
      height: '320px',
    },
  },
  expired: {
    fontSize: '18px',
    fontFamily: '"avenir-heavy","Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif',
    margin: 'auto',
    marginTop: '170px',
    padding: '30px',
    [theme.breakpoints.up('sm')]: {
      fontSize: '20px',
      marginTop: '100px',
    },
    [theme.breakpoints.up('lg')]: {
      fontSize: '24px',
      marginTop: '170px',
    },
  },
  maincont: {
    width: '100%',
    height: '100%',
    textAlign: 'left',
  },
  appLogo: {
    position: 'relative',
    height: '83px',
    left: '-24px',
    [theme.breakpoints.up('lg')]: {
      left: '-16px',
    },
  },
  toolbar: {
    margin: '0px auto',
    width: '100%',
    alignItems: 'initial',
    color: '#FFF',
    backgroundColor: theme.palette.primary.light,
    [theme.breakpoints.up('lg')]: {
      maxWidth: '940px',
      height: '70px',
      color: theme.palette.primary.main,
      backgroundColor: '#FFF',
    },
    [theme.breakpoints.up('xl')]: {
      maxWidth: '1140px',
    },
  },
  appBar: {
    position: 'fixed', // Do not scroll with page. Specify here instead of AppBar position='fixed' property
    marginLeft: DRAWER_WIDTH,
    [theme.breakpoints.up('md')]: {
      // width: `calc(100% - ${DRAWER_WIDTH}px)`,
      width: '100%',
    },
    zIndex: 2000,
    backgroundColor: '#FFF',
    // color: theme.palette.common.white, // Set color of child Button text to inherit
    boxShadow: 'none',
  },
  user: {
    margin: 'auto',
    width: '600px',
    marginRight: '20px',
    textAlign: 'right'
  },
  navIconHide: {
    color: 'white',
    margin: 'auto 30px auto 0px',
    [theme.breakpoints.up('lg')]: {
      display: 'none',
    },
  },
  mobileHide: {
    [theme.breakpoints.down('md')]: {
      display: 'none',
    },
  },
  lgLogout: {
    fontStyle: 'normal',
  },
  avatar: {
    backgroundColor: '#3dacd1',
    // backgroundColor: blue[200],
    // color: blue[600],
    marginRight: theme.spacing(),
  },
  avatarImage: {
    margin: 10,
    // width: 60,
    // height: 60,
  },
  // Style used to position remaining elements to the right (which have no flex value assigned)
  flex: {
    flex: 1,
    textAlign: 'left',
    top: '200px',
  },
  login: {
    fontFamily: '"avenir-heavy","Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif',
    fontStyle: 'normal',
    margin: 'auto 24px',
    height: '34px',
    width: '120px',
    backgroundColor: '#f79c31',
    borderRadius: '25px',
    color: 'white',
    display: 'none',
    [theme.breakpoints.up('lg')]: {
      display: 'block',
    },
  }
});

class AppRoot extends Component {
  constructor(props) {
    super(props);
    this.state = {
      uniqueKey: 0,
      mobileNavOpen: false,
      logonDlgOpen: false,
      timeoutDate: null,
      viewer: new Viewer(),
      whichPage: NAV_DEFAULT,
      inactivityTimer: new UserInactivityTimer(this.getSession),
      inactivityDlgOpen: false,

      sessionID: "",
      accessKey: "",
      expireDT: 0,
      sessionActive: true,

      firstLanding: true
    }
  }

  // Session management
  getSession = async () => {

    // Lookup session ID and access key from local storage in browser
    let sessionID = localStorage.getItem('sessionID') || "";
    let accessKey = localStorage.getItem('accessKey') || "";
    let expireDT = localStorage.getItem('expireDT') || 0;

    // Validate session information with server or get new session
    const { data } = await this.props.client.query({
      query: GET_SESSION,
      variables: { sessionID, accessKey },
      fetchPolicy: "no-cache"
    });

    // Session expired or unavailable
    if (data === null) {
      console.log("Session expired.");
      this.setState({sessionActive: false});
      return;
    }

    // Received session
    sessionID = data.getSession.sessionID;
    accessKey = data.getSession.accessKey;
    expireDT = data.getSession.expireDT;
    localStorage.setItem('sessionID', sessionID);
    localStorage.setItem('accessKey', accessKey);
    localStorage.setItem('expireDT', expireDT);
    this.setState({ sessionID, accessKey, expireDT });
    if (data.getSession.sessionID === sessionID)
      console.log("Extending previous session");
    else
      console.log("Starting new session");
  };

  // Run once page loads
  componentDidMount() {

    // Start user inactivity timer that:
    //  1) Displays dialog before idleCounter timer finished.
    //  2) Logs user out if exceeded, else return back to current page
    this.state.inactivityTimer.start(this.inactivityDialogOpen, this.handleInactivityLogout);

    // Validate session or get new one
    this.getSession();
  }

  // --------------------------
  // User Inactivity methods
  inactivityDialogOpen = (timeoutDate) => {
    // console.log(TAG, 'inactivityDlgOpen: Opening user inactivity dialog...');
    this.setState({ inactivityDlgOpen: true, timeoutDate: timeoutDate });
  };

  inactivityDialogClose = () => {
    // console.log(TAG, 'inactivityDialogClose: Closing user inactivity dialog...');
    this.setState({ inactivityDlgOpen: false, timeoutDate: null }); // Close dialog
  };

  handleInactivityContinue = () => {
    // console.log(TAG, 'handleInactivityContinue: Continuing user session...');
    this.inactivityDialogClose();
    this.state.inactivityTimer.reset();
  };

  handleInactivityLogout = () => {
    // console.log(TAG, 'Ending session');
    this.inactivityDialogClose();
    this.handleLogout();
  };

  handleLogonDlgCancel = () => {
    // console.log(TAG, 'Login cancelled');
    this.setState({ logonDlgOpen: false }); // Close dialog

    // NOTE: User inactivity timer isn't started, so we don't need to stop it
  };

  handleLogonSubmit = async (usr, pwd) => {
    // console.log(TAG, 'handleLogonSubmit: Fetching user...', usr);
    try {
      // Reset the Apollo Client store entirely since a new user is logging in.
      // This is also good in case the user has previous failed login attempts.
      // To accomplish this, use client.resetStore to clear out your Apollo cache.
      // Since client.resetStore also re-fetches any of your active queries for you, it is asynchronous.
      // We have access to the 'client' property since we used withApollo(component) enhancer.
      // Ref: https://www.apollographql.com/docs/react/api/react-apollo.html#withApollo
      // Ref: https://www.apollographql.com/docs/react/advanced/caching.html#reset-store
      // Ref: https://www.apollographql.com/docs/react/recipes/authentication.html#login-logout
      this.props.client.resetStore();

      const viewer = await authenticateViewer(usr, pwd);

      // NOTE: IF CODE GOT HERE, THEN ApolloClient DIDN'T THROW AN ERROR, SO USER IS AUTHENTICATED (FOUND)
      this.setState({ viewer: viewer, logonDlgOpen: false });
      console.debug(TAG, 'GraphQL authenticated user=', viewer.username); // TODO: PROD - Eliminate exposure of sensitive logon info

      // Auto-select first facility, disabling selection. Used for Ventec development
      this.setState(prevState => ({ viewer: prevState.viewer.setCurrentFacilityAndGroup(0) }));

      // Navigate to upload page
      this.setState({ whichPage: NAV_UPLOAD, mobileNavOpen: false });

    } catch (err) {
      console.error(TAG, `handleLogonSubmit: ${err.message}`);
      // this.resetUser(); // NOTE: Appears unnecessary since it remains initialized to empty Viewer & dialog clears

      // TODO: Possibly display flag/message to <LoginDialog/> to inform user to try again? Otherwise remove message
      // Errors such as network error, or GraphQL error (specified resource does not exist), etc.
    }
  };

  enter = () => {
    this.setState({firstLanding: false})
  };

  handleLogout = () => {
    console.log(TAG, 'handleLogout: Logging user out...');

    // Stop user inactivity timer
    this.state.inactivityTimer.stop();

    // Reset the Apollo Client store entirely since the user has logged out.
    // To accomplish this, use client.resetStore to clear out your Apollo cache.
    // Since client.resetStore also re-fetches any of your active queries for you, it is asynchronous.
    // We have access to the 'client' property since we used withApollo(component) enhancer.
    // Ref: https://www.apollographql.com/docs/react/api/react-apollo.html#withApollo
    // Ref: https://www.apollographql.com/docs/react/advanced/caching.html#reset-store
    // Ref: https://www.apollographql.com/docs/react/recipes/authentication.html#login-logout
    this.props.client.resetStore();

    // Clear local storage
    localStorage.setItem('sessionID', "");
    localStorage.setItem('accessKey', "");
    localStorage.setItem('expireDT', "");

    // Make sure state variables are reset to no user, and we're on default page
    // IMPORTANT: Do it atomically in one setState call, or we'll get 2 renders calls.
    // IMPORTANT: Must make sure default page is set before we get default Viewer object
    // (e.g. may still be on RoomConfig page and issue ApolloClient request with default viewer w/no facility, etc.)
    // this.setState({ uniqueKey: 1, whichPage: NAV_DEFAULT, viewer: new Viewer() });
    //
    // NOTE: When the user logs out, we need to ensure that the FacilityMenu Component is reset to its original state
    // (so the selectedIndex is reset to -1 so "Choose Facility" will appear again).
    // The implementation I chose was to take advantage of 'key' attribute trick.
    // This is where you add a key attribute to the root-level component returned by the Component's
    // render(). When the key value changes, it causes the implicit browser state (and the state of its children) to be
    // reset -- which causes children React Components to be thrown away and created from scratch. There's no shortcut
    // to reset the individual component's local state.
    //      render() {
    //          // ...
    //          return <div key={uniqueKey}>
    //              {children}
    //          </div>;
    //      }
    this.setState(prevState => ({ uniqueKey: prevState.uniqueKey + 1, whichPage: NAV_DEFAULT,
      viewer: new Viewer(), sessionActive: false }));
  };


  render() {
    const { classes /* ,theme */ } = this.props;
    const { uniqueKey, logonDlgOpen, inactivityTimer, inactivityDlgOpen, timeoutDate } = this.state;
    const ver_message = "System v" + SYS_VER + "\nWeb App v" + MOD_VER;

    return (
      // NOTE: When using React you should generally not need to call addEventListener to add listeners to a DOM element
      // after it is created. Instead, just provide a listener when the element is initially rendered.
      // Handling Events: https://reactjs.org/docs/handling-events.html
      // SyntheticEvent:  https://reactjs.org/docs/events.html#mouse-events
      // Render Props:    https://reactjs.org/docs/render-props.html
      <div id='appRoot' key={uniqueKey} className={classes.root} onKeyPress={inactivityTimer.reset} onMouseMove={inactivityTimer.reset} >
        <img src="/image/hidden.png" alt={ver_message} title={ver_message} width="20px" height="20px" className={classes.version}/>
        <div className={classes.grayBar} />
        <a href="https://www.venteclife.com/"><img src="/image/vocsn_multi_view_beta_box.png" alt="VOCSN Multi-View" width="240px" height="97" className={classes.logo}/></a>
        {(this.state.sessionActive &&
          <main className={classes.content}>
            <div className={classes.maincont}>
              <BrowserRouter>
                <Switch>
                  {/*<Route path="/upload">*/}
                  {/*  <GuestUpload sessionID={this.state.sessionID} accessToken={this.state.accessKey}*/}
                  {/*               expireDT={this.state.expireDT} resetTimer={this.state.inactivityTimer.reset}*/}
                  {/*               uploadClient={this.props.uploadClient}/>*/}
                  {/*</Route>*/}
                  <Route path="/">

                    {/* Show validation landing message when page first loads if enabled in .env */}
                    { ( this.state.firstLanding &&
                        (( USE_VAL_LANDING &&
                            <ValidationLanding enter={this.enter}/>
                        ) || (
                            <TermsLanding enter={this.enter}/>
                        ))
                    ) || (
                      <GuestUpload sessionID={this.state.sessionID} accessToken={this.state.accessKey}
                                   expireDT={this.state.expireDT} resetTimer={this.state.inactivityTimer.reset}
                                   uploadClient={this.props.uploadClient} useValLanding={USE_VAL_LANDING} />
                    ) }
                  </Route>
                </Switch>
              </BrowserRouter>
            </div>
          </main>
        ) ||
          <div className={classes.expired}>
            Your session has expired. Refresh the page to begin a new session.
          </div>
        }
        <LoginDialog
          isOpen={logonDlgOpen}
          onCancel={this.handleLogonDlgCancel}
          onSubmit={this.handleLogonSubmit}
        />
        <InactivityDialog
          isOpen={inactivityDlgOpen}
          timeoutDate={timeoutDate}
          onContinue={this.handleInactivityContinue}
          onLogout={this.handleInactivityLogout}
          classes={classes}
        />
      </div>
    );
  }
}

// Give access to the 'client' property by wrapping with withApollo(component) enhancer.
export default withApollo(withStyles(styles, { withTheme: true })(AppRoot));
