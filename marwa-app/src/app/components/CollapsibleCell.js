/**
 * Collapsible table cell.
 *
 */
import React from 'react';
import PropTypes from 'prop-types';
import classNames from 'classnames';
import { TableCell} from '@material-ui/core';
import { withStyles } from '@material-ui/core/styles';

const defHeight = 60;

const styles = theme => ({
  collapsible: {
    textAlign: 'center',
    display: 'block',
    overflow: 'hidden',
    height: defHeight.toString() + 'px',
    transition: 'height 0.1s ease-out, opacity 0.1s ease-out',
  },
  arrow: {
    padding: '0px',
    paddingLeft: '4px'
  },
  genCell: {
    width: '10px',
    fontSize: '10px',
    padding: '0pc',
    [theme.breakpoints.up('sm')]: {
      fontSize: '13px',
    },
    [theme.breakpoints.up('md')]: {
      fontSize: '16px'
    },
    [theme.breakpoints.up('lg')]: {
      fontSize: '18px'
    }
  },
  fileCount: {
    position: 'absolute',
    marginLeft: 'calc(18% + 50px)',
    marginTop: '20px',
    fontFamily: '"avenir-heavy","Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif',
    fontSize: '20px',
    color: '#cacbce',
    transition: 'opacity 0.1s ease-out',
  },
  topAlign: {
    verticalAlign: 'top',
  },
  middle: {
    position: 'relative',
    top: '50%',
    transform: 'translateY(-50%)',
  }
});

const checkFirst = (idx, states) => {
  if (states.sortBy === "date")
    return states.dateIndexList.includes(idx);
  else if (states.sortBy === "serial")
    return states.snIndexList.includes(idx);
};

const checkVisibility = (states, idx, left, upload) => {
  let visible = true;
  let first = checkFirst(idx, states);
  if ((left === true) && first) {
    visible = true;
  }
  else if ((left === true) && !first) {
    visible = false;
  }
  else if (states.sortBy === "date") {
    if (upload.export in states.groupExpansion)
      visible = states.groupExpansion[upload.export];
  }
  else if (states.sortBy === "serial") {
    if (upload.sn in states.groupExpansion)
      visible = states.groupExpansion[upload.sn];
  }
  return visible
};

const getFileCount = (states, idx) => {
  if (states.sortBy === "date")
    return states.dateGroupLength[idx];
  else if (states.sortBy === "serial")
    return states.snGroupLength[idx];
};

class CollapsibleCell extends React.Component {

  render() {
    const { classes, states, idx, upload, children, left, refCell, height, fileCount} = this.props;
    const first = checkFirst(idx, states);
    const visible = checkVisibility(states, idx, left, upload);
    const span = 1;
    return <TableCell className={classNames(classes.genCell, (left ? classes.topAlign : ""),
              (left ? classes.arrow : ""))} rowSpan={span}>
            {fileCount && first &&
              <span className={classes.fileCount} style={states.groupExpansion[
                  (states.sortBy === "date") ? upload.export : upload.sn] ? {opacity: '0'} : {opacity: '1'}}>
                                    {getFileCount(states, idx) + " files"}</span>
            }
            <span className={classNames(classes.collapsible)}
                  style={first ? ((visible || refCell)? null : {opacity: 0}) :
                      (visible ? {height: height + 'px'} : {height: 0})}
            >
              <div className={classNames(classes.middle)}>
                {((visible && (first || !refCell)) || (!visible && first)) && children}
              </div>
            </span>
          </TableCell>
  }
}

CollapsibleCell.propTypes = {
  states: PropTypes.object.isRequired,
  idx: PropTypes.number.isRequired,
  upload: PropTypes.object.isRequired,
};

CollapsibleCell.defaultProps = {
  left: false,
  refCell: false,
  fileCount: false,
  height: defHeight,
};

export default withStyles(styles)(CollapsibleCell);
