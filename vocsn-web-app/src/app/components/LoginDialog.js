import React from 'react';
import PropTypes from 'prop-types';
import { withStyles } from '@material-ui/core/styles';
import Button from '@material-ui/core/Button';
import TextField from '@material-ui/core/TextField';
import {
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  withMobileDialog,
} from '@material-ui/core';

import { DEFAULT_USERNAME, DEFAULT_PASSWORD } from '../data/ui_constants';

const styles = theme => ({
  textField: {
    marginLeft: theme.spacing(3),
    marginRight: theme.spacing(3),
    // width: 200,
    // border: '1px solid lightgray',
    // borderRadius: '10px',
  },
});

/**
 * NOTE: This logon dialog based on Material-UI Responsive full-screen Dialog
 * https://material-ui-next.com/demos/dialogs/#responsive-full-screen
 */
class LoginDialog extends React.Component {
  state = {
    username: DEFAULT_USERNAME,
    password: DEFAULT_PASSWORD,
  };

  handleChange = (event) => {
    const { id, value } = event.target;
    this.setState({ [id]: value });
  };

  handleSubmit = () => {
    const { username, password } = this.state;

    // Don't waste bandwidth connecting to server if user tries to submit empty value (probably by accident)
    if (username) {
    this.props.onSubmit(username, password); // "Lift Up State" by calling parent's submit function

    // TODO: Enhance user experience by not resetting TextFields, so dialog won't visibly clear before being dismissed.
    // TODO: However, we do need to clear the dialog if logon attempt fails! So just don't clear it if logon succeeds.
    // TODO: Then, Reset state username & password in lifecycle method (after dialog is dismissed --> isOpen is false?)
    this.setState({ username: DEFAULT_USERNAME, password: DEFAULT_PASSWORD }); // Reset TextFields

      // TODO: 6/11/2018 Disable Submit button to prevent user from submitting multiple times
    }
  };

  // TODO: [DOM] Password field is not contained in a form: (More info: https://goo.gl/9p2vKq) and
  // TODO:   -- see https://material-ui-next.com/demos/text-fields/
  // TODO: Both TextField and Button can't have 'autoFocus' property?
  render() {
    const { fullScreen, classes, isOpen, onCancel } = this.props;
    const { username, password } = this.state;

    return (
      <Dialog
        fullScreen={fullScreen}
        open={isOpen}
        onClose={onCancel}
        aria-labelledby='logon-dialog'
      >
        <DialogTitle id='responsive-dialog-title'>Log-in to your account</DialogTitle>
        <DialogContent>
          <DialogContentText>
            To access special content on this website, please enter your username (email address) and password.
          </DialogContentText>
        </DialogContent>
        <form /* className={classes.container} */ noValidate autoComplete='off'>
          <TextField
            id='username'
            label='Email Address'
            value={username}
            onChange={this.handleChange}
            type='email'
            className={classes.textField}
            margin='normal'
            autoFocus // will be focused during the first mount
          />
          <TextField
            id='password'
            label='Password'
            value={password}
            onChange={this.handleChange}
            type='password'
            autoComplete='current-password'
            className={classes.textField}
            margin='normal' // OR 'none', 'dense'
          />
        </form>
        <DialogActions>
          <Button onClick={this.handleSubmit} color='primary'>
            Logon
          </Button>
          <Button onClick={onCancel} color='primary'>
            Cancel
          </Button>
        </DialogActions>
      </Dialog>
    );
  }
}

LoginDialog.propTypes = {
  fullScreen: PropTypes.bool.isRequired,
  classes: PropTypes.object.isRequired,
  isOpen: PropTypes.bool.isRequired,
  onCancel: PropTypes.func.isRequired,
  onSubmit: PropTypes.func.isRequired,
};

// export default withMobileDialog()(LoginDialog);
export default withMobileDialog()(withStyles(styles)(LoginDialog));
// export default withStyles(styles)(LoginDialog);
// export default withStyles(styles, { withTheme: true })(LoginDialog);

// import { compose } from 'recompose';
// export default compose(
//   withTheme(),
//   withStyles(styles)
// )(Modal);
//
// // raw function chaining:
// export default withTheme()(withStyles(styles)(Modal));
