import React from 'react';
import PropTypes from 'prop-types';
import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  withMobileDialog,
} from '@material-ui/core';

/**
 * NOTE: This user inactivity dialog is based on Material-UI Responsive full-screen Dialog.
 * https://material-ui-next.com/demos/dialogs/#responsive-full-screen
 *
 * NOTE: Stateless Component
 * NOTE 1: Simply returns JSX elements. So no need for curly braces (either use parenthesis or none OK).
 * NOTE 2: Accept 'props' function argument and de-structure it to only receive the specific props we need.
 */
const InactivityDialog = ({ fullScreen, isOpen, onContinue, onLogout, timeoutDate, classes }) => {
  const timeoutTime = timeoutDate ? timeoutDate.toLocaleTimeString('en-US', { hour12: true }) : '';
  return (
    <Dialog
      fullScreen={fullScreen}
      open={isOpen}
      onClose={onContinue}
      aria-labelledby='inactivity-dialog'
      className={classes.inactiveDialog}
    >
      <DialogTitle id='inactivity-dialog-title'>Do you want to continue your session?</DialogTitle>
      <DialogContent>
        <DialogContentText>
          Your session will expire at {timeoutTime} unless you continue. Otherwise, any information you have entered
           will be lost and you will need to reload the page to upload more files.
        </DialogContentText>
      </DialogContent>

      <DialogActions>
        <Button onClick={onContinue} color='primary'>
          Continue Session
        </Button>
        {/*<Button onClick={onLogout} color='secondary'>*/}
        {/*  Logout*/}
        {/*</Button>*/}
      </DialogActions>
    </Dialog>
  );
};

InactivityDialog.propTypes = {
  fullScreen: PropTypes.bool.isRequired,
  isOpen: PropTypes.bool.isRequired,
  onContinue: PropTypes.func.isRequired,
  onLogout: PropTypes.func.isRequired,
  timeoutDate: PropTypes.object,
};

InactivityDialog.defaultProps = {
  timeoutDate: '',
};

export default withMobileDialog()(InactivityDialog);
