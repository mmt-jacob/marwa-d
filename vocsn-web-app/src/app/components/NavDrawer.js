/**
 * Side Drawer - based on Material-UI demo: ResponsiveDrawer.js
 *
 */
import React from 'react';
import PropTypes from 'prop-types';
import { withStyles } from '@material-ui/core/styles';
import Drawer from '@material-ui/core/Drawer';
import Hidden from '@material-ui/core/Hidden';
import NavDrawerMenu from './NavDrawerMenu';

const styles = theme => ({
  drawerFixed: {
    position: 'fixed', // Always stay in same place even if page is scrolled
  },
  fullWidth: {
    width: '100%',
  },
  drawerHeader: {
    // width: DRAWER_WIDTH,
    // height: 144,
    // backgroundColor: 'black',
  },
  drawerPaper: {
    // backgroundColor: 'white', // TODO: move to theme?
    top: '83px',
    width: '100%',
    position: 'relative',
    border: 'none',
    [theme.breakpoints.up('lg')]: {
      top: '0px',
      // width: DRAWER_WIDTH,
      position: 'relative',
      // height: '100%',
    },
  },
});

// Stateless Component
// NOTE 1: Simply returns JSX elements. So no need for curly braces (either use parenthesis or none OK).
// NOTE 2: Accept 'props' function argument and de-structure it to only receive the specific props we need.
const NavDrawer = ({ classes, onLogout, theme, onNavChange, isMobileOpen, onMobileClose, userRole, whichPage }) => {
  // Define which options to display
  const drawer = (
    <React.Fragment>
      <div className={classes.drawerHeader}>

      </div>
      {/* <Divider /> */}
      <NavDrawerMenu onLogout={onLogout} onNavChange={onNavChange} userRole={userRole} whichPage={whichPage} />
    </React.Fragment>
  );
  // <img src={logo} className={classes.drawerLogo} alt='LinQ logo' />

  return (
    <React.Fragment>
      {/* Small screen */}
      <div className={classes.fullWidth}>
        <Hidden lgUp>
          <Drawer
            variant='temporary'
            // anchor={theme.direction !== 'rtl' ? 'right' : 'left'}
            anchor={'top'}
            open={isMobileOpen}
            classes={{
              paper: classes.drawerPaper,
            }}
            onClose={onMobileClose}
            ModalProps={{
              keepMounted: true, // Better open performance on mobile.
            }}
          >
            {drawer}
          </Drawer>
        </Hidden>

        {/* Large screen */}
        <Hidden mdDown implementation='css'>
          <Drawer
            variant='permanent'
            open
            // className={classes.drawerFixed}
            classes={{
              paper: classes.drawerPaper,
            }}
          >
            {drawer}
          </Drawer>
        </Hidden>
      </div>
    </React.Fragment>
  );
};

NavDrawer.propTypes = {
  classes: PropTypes.object.isRequired,
  theme: PropTypes.object.isRequired,
  onNavChange: PropTypes.func.isRequired,
  isMobileOpen: PropTypes.bool.isRequired,
  onMobileClose: PropTypes.func.isRequired,
  userRole: PropTypes.number.isRequired,
};

export default withStyles(styles, { withTheme: true })(NavDrawer);
