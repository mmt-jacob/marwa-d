import React from 'react';
import PropTypes from 'prop-types';
import { withStyles } from '@material-ui/core/styles';
import Typography from '@material-ui/core/Typography';

const styles = theme => ({
  container: {
    marginBottom: theme.spacing(2),
  },
});

// Stateless Component
// NOTE 1: Simply returns JSX elements. So no need for curly braces (either use parenthesis or none OK).
// NOTE 2: Accept 'props' function argument and de-structure it to only receive the specific props we need.
const BigValue = ({ classes, title, value, valueColor }) => {
  const getStyle = () => ({
    color: `${valueColor}`,
    // fontSize: theme.typography.pxToRem(15),
    fontSize: 24,
    fontWeight: 'bold',
  });

  return (
    <div className={classes.container}>
      <Typography variant='body1'>
        {title}
      </Typography>
      <Typography style={getStyle()}>
        {value}
      </Typography>
    </div>
  );
};

BigValue.propTypes = {
  classes: PropTypes.object.isRequired,
  title: PropTypes.string.isRequired,
  value: PropTypes.string.isRequired,
  valueColor: PropTypes.string.isRequired,
};

export default withStyles(styles)(BigValue);
// export default withStyles(styles, { withTheme: true })(BigValue);
