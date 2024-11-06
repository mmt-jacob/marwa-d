import React from 'react';
import PropTypes from 'prop-types';
import { withStyles } from '@material-ui/core/styles';
import {
  Button,
  MenuList,
  MenuItem,
  Paper,
  Popover,
  Typography,
} from '@material-ui/core';

const styles = theme => ({
  // Note: See Default Theme 'title' and 'button' reference to values we use/override here
  // theme.typography.title.*  (fontSize, fontWeight, lineHeight)
  // theme.typography.button.*
  // https://material-ui.com/customization/default-theme/
  root: {
    ...theme.typography.title, // Override fontSize, fontWeight, lineHeight
    color: theme.palette.common.white,
    // background: 'linear-gradient(45deg, #FE6B8B 30%, #FF8E53 90%)',
    background: 'rgba(255, 255, 255, 0.20)',
    borderRadius: 3,
    border: 0,
    // boxShadow: '0 3px 5px 2px rgba(255, 105, 135, .3)',
    // height: 48,
    // padding: '0 30px',
  },
  label: {
    textTransform: 'none', // capitalize | uppercase | lowercase | none | inherit
  },
});

class FacilityMenu extends React.Component {
  state = {
    anchorEl: null,
    selectedIndex: -1,
  };

  getSelectedFacilityGroupLabel = () => {
    const option = this.props.options[this.state.selectedIndex];
    return `${option.facilityName}: ${option.groupName}`;
  };

  handleClickButton = event => {
    this.setState({ anchorEl: event.currentTarget });
    console.log('handleClickButton');
  };

  handleClose = event => {
    console.log('handleClose');
    this.setState({ anchorEl: null });
  };

  // handleIt = () => console.log('Dood it');;
  handleIt = event => {
    console.log('handleIt: event=', event);
    // this.handleClickMenuItem(event, 0);
  };

  handleClickMenuItem = (event, index) => {
    console.log('handleMenuItemClick: index=', index);
    this.setState({ selectedIndex: index, anchorEl: null });
    this.props.onChange(index);
  };

  /**
   *
   * Render States:
   * |---|----------------|----------|----------------|--------------------------------------------------|
   * | # | Facility/Group | Facility | FacilityMenu   | Notes                                            |
   * |   |     Count      |  Chosen  |                |                                                  |
   * |---|----------------|----------|----------------|--------------------------------------------------|
   * | 1 |   undefined    |   n/a    | hide           | No facility to show.                             |
   * | 2 |       0        |   n/a    | hide           | No facility to show.                             |
   * | 3 |       1        |   yes    | show text only | Show facility/group text only.                   |
   * | 4 |      >=1       |   no     | show choose    | Show "Choose Facility" button label.             |
   * | 5 |      >=1       |   yes    | show menu      | Show facility/group choices.                     |
   * |---------------------------------------------------------------------------------------------------|
   *
   * Ref: https://material-ui.com/demos/menus/#menulist-composition
   */
  render() {
    const { classes, myStyle, options } = this.props;
    const { anchorEl, selectedIndex } = this.state;

    console.log('FacilityMenu: options=', options);
    // console.log('FacilityMenu: options.length=', options.length);
    // console.log('FacilityMenu: selectedIndex=', selectedIndex);

    const numOptions = options.length;
    if (numOptions <= 1) {
      return (
        <div className={myStyle}>
          <Typography variant='title' color='inherit'>
            {(numOptions === 0) ? '' : this.getSelectedFacilityGroupLabel()}
          </Typography>
        </div>
      );

    } else {
      return (
        <div className={myStyle}>
          <Button
            classes={{ // Override with classes: https://material-ui.com/customization/overrides/#overriding-with-classes
              root: classes.root, // class name, e.g. `classes-nesting-root-x`
              label: classes.label, // class name, e.g. `classes-nesting-label-x`
            }}
            // aria-owns={anchorEl ? 'my-menu' : null}
            // aria-haspopup='true'
            onClick={this.handleClickButton}
          >
            {(selectedIndex === -1) ? 'Choose which facility' : this.getSelectedFacilityGroupLabel()}
          </Button>
          <Popover
            open={Boolean(anchorEl)}
            anchorEl={anchorEl}
            onClose={this.handleClose}
            // Note: See Anchor Playground: https://material-ui.com/utils/popover/#anchor-playground
            anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
            transformOrigin={{ vertical: 'top', horizontal: 'left' }}
          >
            <Paper>
              <MenuList>
                {options.map((option, index) => (
                  <MenuItem
                    key={option.indexId}
                    selected={index === selectedIndex}
                    onClick={event => this.handleClickMenuItem(event, index)}
                  >
                    {`${option.facilityName}: ${option.groupName}`}
                  </MenuItem>
                  ))}
              </MenuList>
            </Paper>

          </Popover>
        </div>
      );
    }

    // TODO: 8/15/2018 Fix Material-UI: MenuList warning which appears to be caused by onClick value
    // "Warning: Material-UI: the MenuList component doesn't accept a Fragment as a child.
    // Consider providing an array instead."
    // https://github.com/mui-org/material-ui/blob/master/packages/material-ui/src/MenuList/MenuList.js

    // Alternate (working) version which I can't seem to get to position the way I like, so resorted to
    // Popover/MenuList approach instead
    //
    // render() {
    //   const { classes, myStyle, name } = this.props;
    //   const { anchorEl } = this.state;
    //   const open = Boolean(anchorEl);
    //
    //   return (
    //     <div className={myStyle}>
    //       <Button
    //         classes={{ // Overriding w/classes: https://material-ui.com/customization/overrides/#overriding-with-classes
    //           root: classes.root, // class name, e.g. `classes-nesting-root-x`
    //           label: classes.label, // class name, e.g. `classes-nesting-label-x`
    //         }}
    //         aria-owns={anchorEl ? 'my-menu' : null}
    //         aria-haspopup='true'
    //         onClick={this.handleClick}
    //       >
    //         {name || 'Choose a facility'}
    //       </Button>
    //       <Menu
    //         id='my-menu'
    //         // Note: See Anchor Playground: https://material-ui.com/utils/popover/#anchor-playground
    //         anchorEl={anchorEl}
    //         anchorOrigin={{
    //           // vertical: 'top',
    //           horizontal: 'right',
    //         }}
    //         // transformOrigin={{
    //         //   vertical: 'top',
    //         //   horizontal: 'left',
    //         // }}
    //         // transformOrigin='center bottom'
    //         // anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
    //         // transformOrigin={{ vertical: 'bottom', horizontal: 'right' }}
    //         // transformOrigin={{ vertical: 'bottom', horizontal: 'right' }}
    //         open={open}
    //         onClose={this.handleClose}
    //       >
    //         <MenuItem onClick={this.handleClose}>Facility 1</MenuItem>
    //         <MenuItem onClick={this.handleClose}>Facility 2</MenuItem>
    //         <MenuItem onClick={this.handleClose}>Facility 3</MenuItem>
    //       </Menu>
    //     </div>
    //   );
    // }
  }


}

FacilityMenu.propTypes = {
  classes: PropTypes.object.isRequired,
  myStyle: PropTypes.string.isRequired,
  options: PropTypes.array.isRequired,
  onChange: PropTypes.func.isRequired,
};

// export default FacilityMenu;
export default withStyles(styles)(FacilityMenu);
