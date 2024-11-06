/**
 * Responsive Dialog that goes full-screen when on mobile-sized screens.
 */
import React from 'react';
import Button from '@material-ui/core/Button';
import Grid from '@material-ui/core/Grid';
import Checkbox from '@material-ui/core/Checkbox';
import Paper from '@material-ui/core/Paper';
import Radio from '@material-ui/core/Radio';
import RadioGroup from '@material-ui/core/RadioGroup';
import DateFnsUtils from '@date-io/date-fns';
import {
  FormControl,
  FormGroup,
  FormControlLabel,
  Dialog,
  DialogContent,
} from '@material-ui/core';
import classNames from 'classnames';
import MenuItem from '@material-ui/core/MenuItem';
import Input from '@material-ui/core/Input';
import InputLabel from '@material-ui/core/InputLabel';
import Select from '@material-ui/core/Select';
import { withStyles } from '@material-ui/core/styles';
import {
  MuiPickersUtilsProvider,
  KeyboardDatePicker,
} from '@material-ui/pickers';

import {
  OPTIONS_PERIOD,
  roundDayDown,
  getHours, getHours24,
  displayEndDate,
  Sections,
  HoursStart, HoursEnd,
  HOUR_MILLIES, DAY_MILLIES,
} from '../data/ui_constants';


const styles = theme => ({
  formContainer: {
    display: 'flex',
    flexWrap: 'wrap',
  },
  paper: {
    paddingLeft: theme.spacing() * 2,
    paddingRight: theme.spacing() * 2,
    boxShadow: 'none',
    color: theme.palette.text.secondary,
  },
  blueBorder: {
    '& > div:nth-child(3)': {
      '& > div': {
        borderRadius: '20px',
        border: '7px',
        borderStyle: 'solid',
        borderColor: theme.palette.primary.main,
        width: 'calc(460px + 30%)',
        maxWidth: 'none',
        boxShadow: 'none'
      }
    },
    '& > div.MuiBackdrop-root': {
      backgroundColor: 'rgb(0, 0, 0, 0.2)',
    }
  },
  noBorder: {
    '& div:nth-child(2)': {
      border: 'none'
    }
  },
  formGroup: {
    display: 'block',
  },
  formItem: {
    width: '100%',
  },
  normalText: {
    '& span': {
      fontSize: '15px',
      fontFamily: '"avenir-roman","Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif',
      [theme.breakpoints.up('sm')]: {
        fontSize: '18px',
      },
      [theme.breakpoints.up('md')]: {
        fontSize: '21px'
      },
      [theme.breakpoints.up('lg')]: {
        fontSize: '24px'
      }
    }
  },
  mainTitle: {
    fontSize: '22px',
    [theme.breakpoints.up('md')]: {
      fontSize: '28px',
    },
    [theme.breakpoints.up('xl')]: {
      fontSize: '36px',
    },
    fontFamily: '"avenir-black","Segoe UI Black",Roboto,"Helvetica Neue",Arial,sans-serif',
    color: '#57585A',
  },
  title: {
    margin: theme.spacing(),
    textAlign: 'center',
  },
  spaceBelow: {
    marginBottom: '20px',
  },
  formControl: {
    width: 'calc(100% - 25px)',
    margin: '0px',
    minWidth: 120,
  },
  label: {
    lineHeight: '40px',
    transform: 'none',
    paddingRight: '10px',
    position: 'static',
    fontSize: '16px',
    fontFamily: '"avenir-roman","Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif',
    [theme.breakpoints.up('sm')]: {
      fontSize: '18px',
    },
    [theme.breakpoints.up('md')]: {
      fontSize: '22px'
    },
    [theme.breakpoints.up('lg')]: {
      fontSize: '24px'
    }
  },
  orangeButton: {
    borderRadius: '50px',
    fontFamily: '"avenir-heavy","Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif',
    fontStyle: 'normal',
    textTransform: 'capitalize',
    color: 'white',
    backgroundColor: theme.palette.ternary.main,
    // This is experimental
    '&:hover': {
      backgroundColor: theme.palette.ternary.light,
      // Reset on touch devices, it doesn't add specificity
      '@media (hover: none)': {
        // This toggles after clicks
        backgroundColor: theme.palette.ternary.main,
      },
    },
    '&:disabled': {
      color: theme.palette.disabled.light,
      backgroundColor: theme.palette.disabled.dark,
    }
  },
  midButton: {
    fontSize: '14px',
    padding: '0px 16px',
    [theme.breakpoints.up('sm')]: {
      fontSize: '18px',
      padding: '0px 20px',
    },
    [theme.breakpoints.up('md')]: {
      fontSize: '18px',
      padding: '0px 24px',
    },
    [theme.breakpoints.up('lg')]: {
      fontSize: '22px',
      padding: '0px 28px',
    }
  },
  selectBorder: {
    width: '100%',
    margin: '0px',
    borderRadius: 20,
    position: 'relative',
    backgroundColor: theme.palette.background.paper,
    border: '2px solid #a8a9ad',
    padding: '3px 0px 3px 13px',
    transition: theme.transitions.create(['border-color', 'box-shadow', "color"]),
    '&:before': {
      display: 'none',
    },
    '& div::before, div::after': {
      content: 'none',
    },
    '& div': {
      width: '100%',
      paddingRight: '0px !important',
      background: 'none !important',
      '& div': {
        fontSize: '14px',
        paddingBottom: '0px',
        fontFamily: '"avenir-roman","Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif',
        [theme.breakpoints.up('sm')]: {
          fontSize: '15px',
        },
        [theme.breakpoints.up('lg')]: {
          fontSize: '16px'
        },
        [theme.breakpoints.up('xl')]: {
          fontSize: '18px'
        },
        '&:focus': {
          borderColor: 'white',
        }
      }
    }
  },
  disabledBorder: {
    color: '#efeff0',
    border: '2px solid #efeff0 !important',
  },
  datePick: {
    '& > div': {
      '& > input': {
        width: '250%'
      }
    }
  },
  textField: {
    margin: theme.spacing(),
    minWidth: 120,
  },
  alignCell: {
    padding: '0px',
    border: 'none',
    width: '55px',
  },
  shrink: {
    transformOrigin: 'top left',
    transform: 'translate(0, 1.5px) scale(0.75)'
  },
  moveDown: {
    marginTop: '16px'
  }
});

class ReportOptionsDialog extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      dirty: false,
      from: 'Export',
      startOpen: false,
      endOpen: false,
      selectedFiles: [],
      source: this.props.reportOptions.source,
      start: this.props.start,
      end: this.props.end,
      displayEnd: displayEndDate(this.props.end),
      period: this.props.reportOptions.period,
      sections: this.props.reportOptions.sections,
    };
  }

  // getDerivedStateFromProps
  // Initialize the state variables with the next property object
  // NOTE: Invoked before a mounted component receives new props. To update state in response to prop changes (e.g. to
  // reset it), you may compare this.props & nextProps, and perform state transitions using setState() in this method.
  static getDerivedStateFromProps(nextProps, state) {
    const {reportOptions, selectedFiles} = nextProps;
    let now = new Date();
    let end = new Date(now.getFullYear(), now.getMonth(), now.getDate(), now.getHours()+1);
    let displayEnd = displayEndDate(end);
    let duration = reportOptions.period.hours * HOUR_MILLIES;
    let start = new Date(end.getTime() - duration);
    if (!state.dirty) {
      return{
        from: "Export",
        selectedFiles: selectedFiles(),
        source: reportOptions.source,
        start,
        end,
        displayEnd,
        period: reportOptions.period,
        sections: Object.create(reportOptions.sections)
      }
    }
    return null;
  }

  getDuration = (per) => {
    return per.hours * HOUR_MILLIES;
  };

  getStartMax = () => {
    let nextHour = this.endOfHour();
    return new Date(nextHour - this.getDuration(this.state.period));
  };

  endOfHour = () => {
    let now = new Date();
    return new Date(now.getFullYear(), now.getMonth(), now.getDate(), now.getHours()+1);
  };

  validHour = (dt, hour, per = null) => {
    let nextHour = this.endOfHour();
    let ref_date = new Date(dt.getFullYear(), dt.getMonth(), dt.getDate(), hour);
    if (per) {
      let offset = this.getDuration(per);
      nextHour = new Date(nextHour.getTime() - offset);
    }
    return ref_date <= nextHour;
  };

  constrainEnd = (dt) => {
    let nextHour = this.endOfHour();
    return new Date(Math.min(dt.getTime(), nextHour.getTime()));
  };

  constrainStart = (dt, dur = null) => {
    if (dt === null)
      return;
    dur = dur ? dur : this.state.period;
    dur = this.getDuration(dur);
    let end = new Date(dt.getTime() + dur);
    end = this.constrainEnd(end);
    return new Date(end.getTime() - dur);
  };

  handleChangePeriod = (event) => {
    const per = event.target.value;
    let duration = this.getDuration(per);
    let start = this.state.start;
    let end = this.state.end;
    if (this.state.from === "Start") {
      end = new Date(start.getTime() + duration);
      end = this.constrainEnd(end);
      start = new Date(end.getTime() - duration);
    } else {
      start = new Date(end.getTime() - duration);
      start = this.constrainStart(start, per);
      end = new Date(start.getTime() + duration);
    }
    // if (per.code >= 4) {
    //   start = roundDayDown(start);
    //   end = roundDayDown(end);
    // }
    let displayEnd = displayEndDate(end);
    this.setState({period: per, start, end, displayEnd, dirty: true});
  };

  handleChangeChecked = (keyName, value, event, checked) => {
    let sections = this.state.sections;
    let found = false;
    for (let i = 0; i < sections.length; i++) {
      if (sections[i] === value) {
        if (!checked) {
          sections.splice(i, 1);
          found = true;
          break;
        }
      }
    }
    if (!found && checked) {
      sections = [...sections, value];
      sections.sort();
    }
    this.setState({sections: sections, dirty: true});
  };

  handleChangeStart = (start) => {
    if (start === null)
      return;
    let duration = this.getDuration(this.state.period);
    start = this.constrainStart(start);
    let end = new Date(start.getTime() + duration);
    let displayEnd = displayEndDate(end);
    this.setState({start, end, displayEnd, startOpen: false, dirty: true});
  };

  handleChangeEnd = (displayEnd) => {
    if (displayEnd === null)
      return;
    let hourIndex = displayEnd.getHours();
    let end = displayEnd;
    if (hourIndex === 0)
      end = new Date(displayEnd.getTime() + DAY_MILLIES);
    end = this.constrainEnd(end);
    displayEnd = displayEndDate(end);
    let duration = this.getDuration(this.state.period);
    let start = new Date(end.getTime() - duration);
    this.setState({end, displayEnd, start, endOpen: false, dirty: true});
  };

  handleChangeStartHour = (event) => {
    let value = event.target.value;
    let start = this.state.start;
    let duration = this.getDuration(this.state.period);
    start = this.constrainStart(start);
    let offset = value.code * HOUR_MILLIES;
    start = roundDayDown(start);
    start = new Date(start.getTime() + offset);
    let end = new Date(start.getTime() + duration);
    let displayEnd = displayEndDate(end);
    this.setState({start, end, displayEnd, dirty: true});
  };

  handleChangeEndHour = (event) => {
    let value = event.target.value;
    let end = this.state.end;
    end = this.constrainEnd(end);
    let duration = this.getDuration(this.state.period);
    let offset = value.code * HOUR_MILLIES;
    if (end.getHours() !== 0)
      end = roundDayDown(end);
    else
      end = new Date(end.getTime() - DAY_MILLIES);
    end = new Date(end.getTime() + offset);
    let start = new Date(end.getTime() - duration);
    let displayEnd = displayEndDate(end);
    this.setState({start, end, displayEnd, dirty: true});
  };

  toggleStart = () => {
    let current = this.state.startOpen;
    this.setState({startOpen: !current, dirty: true});
  };

  toggleEnd = () => {
    let current = this.state.endOpen;
    this.setState({endOpen: !current, dirty: true});
  };

  handleRadio = (event) => {
    let from = event.target.value;
    this.setState({from, dirty: true});
  };

  // Close window
  handleCancel = () => {
    console.log("Cancel options dialog.");
    this.setState({dirty: false});
    this.props.onClose();
  };

  // Begin upload
  acceptOptions = () => {

    // Validate date date pickers
    let start = document.getElementById("start-id");
    let end = document.getElementById("end-id");
    if (document.getElementById("start-id-helper-text") ||
        document.getElementById("end-id-helper-text") ||
        (start && start.value === "") ||
        (end && end.value === "")) {
      window.alert("Please enter a valid start and end date.");
      return
    }

    // Close dialog and return to page
    console.log("Accept options dialog.");
    this.setState({dirty: false});
    this.props.onAccept(this.state);
  };

  render() {
    const { classes, open } = this.props;

    return (
      <Dialog
        open={open}
        onClose={this.handleCancel}
        aria-labelledby='report-configuration-dialog'
        className={classes.blueBorder}
      >
        <DialogContent>
          <form className={classes.formContainer}>
            <Grid container style={{marginBottom: '0px'}}>

              {/* Report Section Selection */}
              <Grid item xs={12} md={5}>
                <Paper className={classes.paper}>
                  <div className={classNames(classes.mainTitle, classes.spaceBelow)}>
                    Report Sections
                  </div>

                  {/* Report Sections */}
                  <FormControl component='fieldset'>
                    <FormGroup row className={classes.formGroup}>
                      {Object.keys(Sections).map((section) => (
                          <FormControlLabel
                              className={classNames(classes.formItem, classes.normalText)}
                              key={section}
                              control={
                                <Checkbox
                                    onChange={this.handleChangeChecked.bind(this, section, Sections[section])}
                                    // checked={((parseInt(this.state.period.code, 10) <= 4) &&
                                    //     (Sections[section] === Sections.TREND))? false :
                                    //     this.state.sections.some(item => Sections[section] === item)}
                                    // disabled={(parseInt(this.state.period.code, 10) <= 4) &&
                                    //     (Sections[section] === Sections.TREND)}
                                    checked={this.state.sections.some(item => Sections[section] === item)}
                                    value={section} color='primary'
                                />
                              }
                              label={Sections[section].label}
                          />
                      ))}
                    </FormGroup>
                  </FormControl>

                </Paper>
              </Grid>

              {/* Date range settings */}
              <Grid item xs={12} md={7}>
                <Grid container>
                  <Paper className={classes.paper}  style={{width: '100%'}}>
                    <div className={classNames(classes.mainTitle, classes.spaceBelow)}>
                      Report Duration
                    </div>

                    {/* Report Period */}
                    <FormControl className={classes.formControl}>
                      <Grid container>
                        <Grid item xs={3} className={classes.alignCell}>
                          <InputLabel className={classNames(classes.formItem, classes.label)}
                                      htmlFor='period-id'>Period</InputLabel>
                        </Grid>
                        <Grid item xs={9} className={classes.alignCell} style={{width:'80%'}}>
                          <Select
                            disableUnderline
                            value={this.state.period}
                            onChange={this.handleChangePeriod}
                            input={<Input className={classNames(classes.selectBorder)} name='period' id='period-id' />}
                          >
                            {OPTIONS_PERIOD.map(x => <MenuItem key={x.code} value={x}>{x.label}</MenuItem>)}
                          </Select>
                        </Grid>
                      </Grid>
                    </FormControl>

                    {/* Period anchor "from" */}
                    <FormControl className={classes.formControl}>
                      <Grid container>
                        <Grid item xs={3}/>
                        <Grid item xs={9}>
                          <RadioGroup aria-label="from date" name="From Date" defaultValue='Export'
                                      onChange={this.handleRadio} style={{flexDirection: 'row'}}>
                            <FormControlLabel
                                value="Start"
                                label="Choose Start"
                                labelPlacement="start"
                                control={<Radio color="primary" />}
                                style={{width: '45%', flexDirection: 'row'}}
                            />
                            <FormControlLabel
                                value="End"
                                label="Choose End"
                                labelPlacement="start"
                                control={<Radio color="primary" />}
                                style={{width: '45%', flexDirection: 'row'}}
                            />
                            <FormControlLabel
                                value="Export"
                                label="End at Export Time"
                                labelPlacement="start"
                                control={<Radio color="primary" />}
                                style={{flexDirection: 'row'}}
                            />
                          </RadioGroup>
                        </Grid>
                      </Grid>
                    </FormControl>
                  </Paper>
                </Grid>

                {/* Date range and timezone settings */}
                {this.state.from !== "Export" &&
                  <Grid style={{marginTop: '30px'}}>
                    <Paper className={classes.paper}>
                      <div className={classNames(classes.mainTitle, classes.spaceBelow)}>
                        Date Range
                      </div>

                      {/* Start Date */}
                      <FormControl className={classes.formControl} style={{marginBottom: '20px'}}>
                        <Grid container>
                          <Grid item xs={3} className={classes.alignCell}>
                            <InputLabel className={classNames(classes.formItem, classes.label)}
                                        htmlFor='start-date'>Start</InputLabel>
                          </Grid>
                          <Grid item xs={6} className={classes.alignCell} style={{width: '80%'}}>
                            <MuiPickersUtilsProvider utils={DateFnsUtils}>
                              <KeyboardDatePicker
                                  style={{width: '90%'}}
                                  className={classNames(classes.selectBorder, classes.datePick, (this.state.from !== "Start" && classes.disabledBorder))}
                                  variant="inline"
                                  margin="normal"
                                  id="start-id"
                                  format="MM/dd/yyyy"
                                  value={this.state.start}
                                  open={this.state.startOpen}
                                  onOpen={this.toggleStart}
                                  onClose={this.toggleStart}
                                  onChange={this.handleChangeStart}
                                  disabled={this.state.from !== "Start"}
                                  KeyboardButtonProps={{
                                    'aria-label': 'start date',
                                  }}
                                  maxDate={this.getStartMax()}
                              />
                            </MuiPickersUtilsProvider>
                          </Grid>
                          <Grid item xs={3} className={classes.alignCell}>
                            <Select
                                disableUnderline
                                onChange={this.handleChangeStartHour}
                                value={this.state.start ? HoursStart[getHours(this.state.start)] : HoursStart[0]}
                                disabled={this.state.from !== "Start"}
                                input={<Input className={classNames(classes.selectBorder,
                                    ((this.state.from !== "Start") && classes.disabledBorder))}
                                              name='start-time' id='start-time-id'/>}
                            >
                              {HoursStart.map(x =>
                                  <MenuItem key={x.code} value={x}
                                            disabled={!this.validHour(this.state.start, x.code, this.state.period)}>
                                    {x.label}
                                  </MenuItem>)}
                            </Select>
                          </Grid>
                        </Grid>
                      </FormControl>

                      {/* End Date */}
                      <FormControl className={classes.formControl}>
                        <Grid container>
                          <Grid item xs={3} className={classes.alignCell}>
                            <InputLabel className={classNames(classes.formItem, classes.label)}
                                        htmlFor='end-date'>End</InputLabel>
                          </Grid>
                          <Grid item xs={6} className={classes.alignCell} style={{width: '80%'}}>
                            <MuiPickersUtilsProvider utils={DateFnsUtils}>
                              <KeyboardDatePicker
                                  style={{width: '90%'}}
                                  className={classNames(classes.selectBorder, classes.datePick,
                                      (this.state.from !== "End" && classes.disabledBorder))}
                                  variant="inline"
                                  margin="normal"
                                  id="end-id"
                                  format="MM/dd/yyyy"
                                  value={this.state.displayEnd}
                                  open={this.state.endOpen}
                                  onOpen={this.toggleEnd}
                                  onClose={this.toggleEnd}
                                  onChange={this.handleChangeEnd}
                                  disabled={this.state.from !== "End"}
                                  KeyboardButtonProps={{
                                    'aria-label': 'end date',
                                  }}
                                  maxDate={new Date()}
                              />
                            </MuiPickersUtilsProvider>
                          </Grid>
                          <Grid item xs={3} className={classes.alignCell}>
                            <Select
                                disableUnderline
                                onChange={this.handleChangeEndHour}
                                value={this.state.end ? HoursEnd[getHours24(this.state.end)] : HoursEnd[23]}
                                disabled={this.state.from !== "End"}
                                input={<Input className={classNames(classes.selectBorder,
                                    ((this.state.from !== "End") && classes.disabledBorder))}
                                              name='end-time' id='end-time-id'/>}
                            >
                              {HoursEnd.map(x =>
                                  <MenuItem key={x.code} value={x}
                                            disabled={!this.validHour(this.state.end, x.code)}>
                                    {x.label}
                                  </MenuItem>)}
                            </Select>
                          </Grid>
                        </Grid>
                      </FormControl>

                    </Paper>
                  </Grid>
                }
              </Grid>

            </Grid>
          </form>
        </DialogContent>
        <div style={{textAlign: 'center'}}>
            <span className={classes.label}>
              {this.state.selectedFiles.length} Files Selected
            </span>
        </div>
        <div  style={{textAlign: 'center', marginBottom: '20px'}}>
          <Button onClick={this.handleCancel} color='primary' style={{margin: '10px'}}>
            Cancel
          </Button>
          <Button className={classNames(classes.orangeButton, classes.midButton)}
                  onClick={this.acceptOptions}>
            Create Reports
          </Button>
        </div>
      </Dialog>
    );
  }
}

// NOTE: Use 'withStyles' when you want to provide styles through the Material-UI 'classes' object.
// export default withStyles(styles)(RoomConfigDialog);
// export default withStyles(styles, { withTheme: true })(RoomConfigDialog);
export default (withStyles(styles, { withTheme: true })(ReportOptionsDialog));
