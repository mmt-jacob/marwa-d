/**
 * NOTE: Based on Material-UI doc demo "menus/ListItemComposition.js"
 */
import React from 'react';
import PropTypes from 'prop-types';
import classNames from 'classnames';
import { withStyles } from '@material-ui/core/styles';
import { MenuList, MenuItem, ListItemText, Paper } from '@material-ui/core';

import {
  NAV_HOME,
  NAV_UPLOAD,
  NAV_REPORTS,
  DB_USERROLE_GUEST,
  DRAWER_WIDTH,
} from '../data/ui_constants';

const styles = theme => ({
  menuPaper: {
    boxShadow: 'none',
  },
  menuItem: {
    borderBottom: '1px solid #DCDCDC',
    [theme.breakpoints.up('lg')]: {
      width: DRAWER_WIDTH,
      float: 'left',
      borderBottom: 'none',
    },
  },
  primary: {
    textAlign: 'center',
  },
  icon: {},
  mobileOnly: {
    borderTop: '1px solid #8b8e94',
    [theme.breakpoints.up('lg')]: {
      display: 'none'
    }
  }
});

/**
 * NavDrawerMenu
 * NOTE 1: Stateless Component (accept 'props' argument (de-structured) and simply return JSX elements).
 * Here the function arguments are de-structured to only receive the specific props we need.
 * NOTE 2: Only returning JSX elements, so no need for curly braces (either parenthesis or none OK).
 * @param classes
 * @param onLogout
 * @param onNavChange
 * @param userRole
 * @param whichPage
 * @returns {*}
 * @constructor
 */
const NavDrawerMenu = ({ classes, onLogout, onNavChange, userRole, whichPage }) => (
  <Paper className={classes.menuPaper}>
    <MenuList>
      {/*{whichPage !== NAV_HOME &&*/}
      {/*  <React.Fragment>*/}

      {/*  </React.Fragment>*/}
      {/*}*/}
      {userRole > DB_USERROLE_GUEST && whichPage !== NAV_UPLOAD &&
      <MenuItem
          className={classes.menuItem}
          onClick={onNavChange(NAV_UPLOAD)}
          selected={whichPage === NAV_UPLOAD /* && userRole !== DB_USERROLE_GUEST */}
      >
        {/*<ListItemIcon className={classes.icon}><Home /></ListItemIcon>*/}
        <ListItemText classes={{primary: classes.primary}} primary={NAV_UPLOAD}/>
      </MenuItem>
      }
      {userRole > DB_USERROLE_GUEST && whichPage !== NAV_UPLOAD &&
        <MenuItem
            className={classes.menuItem}
            onClick={onNavChange(NAV_REPORTS)}
            selected={whichPage === NAV_REPORTS}
        >
          {/*<ListItemIcon className={classes.icon}><Dashboard /></ListItemIcon>*/}
          <ListItemText classes={{primary: classes.primary}} primary={NAV_REPORTS}/>
        </MenuItem>
      }
      {userRole > DB_USERROLE_GUEST && whichPage !== NAV_UPLOAD &&
        <MenuItem
            className={classNames(classes.menuItem, classes.mobileOnly)}
            onClick={onNavChange(onLogout)}
        >
          {/*<ListItemIcon className={classes.icon}><Dashboard /></ListItemIcon>*/}
          <ListItemText classes={{primary: classes.primary}} primary='LOGOUT'/>
        </MenuItem>
      }
    </MenuList>
  </Paper>
);

NavDrawerMenu.propTypes = {
  classes: PropTypes.object.isRequired,
  onNavChange: PropTypes.func.isRequired,
  userRole: PropTypes.number.isRequired,
  whichPage: PropTypes.string,
};

NavDrawerMenu.defaultProps = {
  whichPage: NAV_HOME,
};

// export default withStyles(styles)(NavDrawerMenu);
export default withStyles(styles, { withTheme: true })(NavDrawerMenu);
