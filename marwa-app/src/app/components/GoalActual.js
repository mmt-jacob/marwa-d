import React from 'react';
import PropTypes from 'prop-types';
import Grid from '@material-ui/core/Grid';
import Typography from '@material-ui/core/Typography';
import { withStyles } from '@material-ui/core/styles';
import { COLOR_BLACK, COLOR_GREEN, /* COLOR_YELLOW, */ COLOR_RED } from '../data/ui_constants';

const styles = theme => ({
  container: {
    marginBottom: theme.spacing(2),
  },
  bigTextBlack: {
    color: `${COLOR_BLACK}`,
    // fontSize: theme.typography.pxToRem(15),
    fontSize: 18,
    fontWeight: 'bold',
  },
});

// Stateless Component
// NOTE 1: Simply returns JSX elements. So no need for curly braces (either use parenthesis or none OK).
// NOTE 2: Accept 'props' function argument and de-structure it to only receive the specific props we need.
const GoalActual = ({ classes, title, goal, actual, fmtstr, goodIsHigher, }) => {
  const getGoal = () => {
    return (fmtstr === undefined) ? goal : fmtstr(goal);
  };

  const getActual = () => {
    return (fmtstr === undefined) ? actual : fmtstr(actual);
  };

  const getStyle = (calcColor) => {
    let textColor = COLOR_BLACK;
    if (calcColor) {
      if (goodIsHigher) {
        textColor = (actual >= goal) ? COLOR_GREEN : COLOR_RED;
      } else {
        textColor = (actual <= goal) ? COLOR_GREEN : COLOR_RED;
      }
    }

    return {
      color: `${textColor}`,
      // fontSize: theme.typography.pxToRem(15),
      fontSize: 18,
      fontWeight: 'bold',
    };
  };

  return (
    <div className={classes.container}>
      <Typography variant='body1'>{title}</Typography>
      <Grid container justify='center'>
        <Grid item>
          <Typography variant='caption'>Goal</Typography>
          <Typography style={getStyle(false)}>
            {getGoal()}
          </Typography>
        </Grid>
        <Grid item>
          <Typography variant='caption'>Actual</Typography>
          <Typography style={getStyle(true)}>
            {getActual()}
          </Typography>
        </Grid>
      </Grid>
    </div>
  );
};

GoalActual.propTypes = {
  classes: PropTypes.object.isRequired,
  title: PropTypes.string.isRequired,
  goal: PropTypes.number.isRequired,
  actual: PropTypes.number.isRequired,
  fmtstr: PropTypes.func,
  goodIsHigher: PropTypes.bool,
};

GoalActual.defaultProps = {
  fmtstr: undefined,
  goodIsHigher: false,
};

// TODO: Add default prop for goodIsHigher

export default withStyles(styles)(GoalActual);
// export default withStyles(styles, { withTheme: true })(Dashboard);
