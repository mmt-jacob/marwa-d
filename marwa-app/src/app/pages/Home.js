import React from 'react';
import PropTypes from 'prop-types';
import { Button } from '@material-ui/core';
import { withStyles } from '@material-ui/core/styles';
import Typography from '@material-ui/core/Typography';
import LoginDialog from "../components/LoginDialog";
import {themePalette} from "../data/ui_constants";
import AppRoot from "../AppRoot";

const styles = theme => ({
  bgimage: {
    width: '100%',
  },
  unitimg: {
    position: 'relative',
    margin: '10% 25%',
    maxWidth: '50%',
    maxHeight: '50%',
    float: 'right',
    [theme.breakpoints.up('sm')]: {
      margin: '0 10%',
    },
    [theme.breakpoints.up('lg')]: {
      maxWidth: '60%',
      maxHeight: '50%',
      margin: '0 calc((100% - 940px) / 2)',
      bottom: '-5%',
    },
    [theme.breakpoints.up('xl')]: {
      margin: '0 calc((100% - 1140px) / 2)',
      maxHeight: '60%',
    },
  },
  imgcont: {
    position: 'absolute',
    top: '70px',
    bottom: '25%',
    left: '0px',
    right: '0px',
    backgroundImage: 'radial-gradient(100% 100% at bottom right, white, #8B8E94)',
    zIndex: '-1',
  },
  content: {
    width: '100%',
    height: '100%',
    margin: '0 auto',
    [theme.breakpoints.up('lg')]: {
      maxWidth: '940px',
    },
    [theme.breakpoints.up('xl')]: {
      maxWidth: '1140px',
    },
  },
  title: {
    fontSize: '26px',
    fontFamily: '"avenir-heavy","Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif',
    margin: '0px 24px',
    paddingTop: '35px',
    color: 'white',
    [theme.breakpoints.up('md')]: {
      paddingTop: '550px',
      fontSize: '30px',
      marginLeft: '0px',
      marginRight: '0px',
    },
    [theme.breakpoints.up('lg')]: {
      paddingTop: '70px',
      fontSize: '36px',
      marginLeft: '0px',
      marginRight: '0px',
    },
  },
  text: {
    fontSize: '12px',
    margin: '0 24px',
    fontFamily: '"avenir-light","Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif',
    color: 'white',
    width: '80%',
    [theme.breakpoints.up('md')]: {
      width: '70%',
      fontSize: '16px',
    },
    [theme.breakpoints.up('lg')]: {
      width: '50%',
      margin: '0px',
      fontSize: '20px',
    },
  },
  login: {
    fontFamily: '"avenir-heavy","Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif',
    margin: '12px 24px',
    backgroundColor: '#f79c31',
    borderRadius: '25px',
    color: 'white',
    display: 'block',
    [theme.breakpoints.up('lg')]: {
      display: 'none',
    },
  }
});

class Home extends React.Component {
  // // NOTE: Use Property Initializer to initialize our component's state instead of using the constructor.
  // state = {
  //   myData: [],
  // };


  render() {
    const { classes, loginRef /* , theme */ } = this.props;

    return (
      <React.Fragment>
        <div className={classes.imgcont}/>
        <div className={classes.content}>
          <Typography variant='title' className={classes.title}>
            Welcome to VOCSN Reports
          </Typography>
          <Typography variant='body1' className={classes.text}>
            Run detailed reports showing utilization, configuration, alarms, and monitored patient data.
          </Typography>
          {!loginRef.auth &&
              <Button className={classes.login} onClick={loginRef.logon}>LOGIN</Button>
          }
          <LoginDialog
              className={classes.login}
              isOpen={loginRef.open}
              onCancel={loginRef.cancel}
              onSubmit={loginRef.submit}
          />
          <img src='/image/vocsn-unit-large.png' className={classes.unitimg} alt='' />
        </div>
      </React.Fragment>
    );
  }
}
// <img src='/image/home-bg.png' className={classes.bgimage} alt='' />

Home.propTypes = {
  classes: PropTypes.object.isRequired,
  // theme: PropTypes.object.isRequired,
};

// NOTE: Use 'withStyles' when you want to provide styles through the Material-UI 'classes' object.
export default withStyles(styles, { withTheme: true })(Home);
