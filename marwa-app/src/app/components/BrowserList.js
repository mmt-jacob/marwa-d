/**
 * Compatible Browser List with Icons
 *
 */
import React from 'react';
import classNames from 'classnames';
import { withStyles } from '@material-ui/core/styles';

const styles = theme => ({
    listDiv: {
        width: '84px',
        height: '130px',
        color: '#57585A',
        fontSize: '14px',
        margin: 'auto',
        lineHeight: '26px',
        fontFamily: '"avenir-black","Segoe UI Black",Roboto,"Helvetica Neue",Arial,sans-serif',
        [theme.breakpoints.up('sm')]: {
            height: '160px'
        },
        [theme.breakpoints.up('md')]: {
            width: '100px',
            height: '180px',
            fontSize: '16px',
            lineHeight: '28px',
        },
        [theme.breakpoints.up('lg')]: {
            width: '120px',
            height: '200px',
            fontSize: '20px',
            lineHeight: '34px',
        }
    },
    spacer: {
        marginLeft: '5px',
        textAlign: 'left'
    },
    noLogo: {
        float: 'left',
        clear: 'left',
        height: '24px',
        width: '14px',
        [theme.breakpoints.up('lg')]: {
            height: '30px',
            width: '20px',
        }
    },
    browserLine: {
        
    },
    browserImgCont: {
        float: 'left',
        clear: 'left',
        height: '24px',
        width: '24px',
        [theme.breakpoints.up('lg')]: {
            height: '30px',
            width: '30px',
        }
    },
    browserImg: {
        height: '20px',
        width: '20px',
        margin: '2px',
        [theme.breakpoints.up('lg')]: {
            height: '24px',
            width: '24px',
            margin: '3px',
        }
    },
    browserName: {
        height: '26px',
        [theme.breakpoints.up('sm')]: {
            height: '30px',
        },
        float: 'left'
    }
});


class BrowserList extends React.Component {

    render() {
        const useLogos = false;
        const { classes} = this.props;
        return <div className={classNames(classes.listDiv)}>
            <div className={classNames(classes.spacer)}>
                <div className={classNames(classes.browserLine)}>
                    <div className={classNames(useLogos ? classes.browserImgCont : classes.noLogo)}>
                        { useLogos && <img alt="" src="/image/browsers/chrome.jpg" className={classes.browserImg}/>}
                    </div>
                    <span className={classes.browserName}>Chrome</span>
                </div>
                <div className={classNames(classes.browserLine)}>
                    <div className={classNames(useLogos ? classes.browserImgCont : classes.noLogo)}>
                        { useLogos && <img alt="" src="/image/browsers/firefox.jpg" className={classes.browserImg}/>}
                    </div>
                    <span className={classes.browserName}>Firefox</span>
                </div>
                <div className={classNames(classes.browserLine)}>
                    <div className={classNames(useLogos ? classes.browserImgCont : classes.noLogo)}>
                        { useLogos && <img alt="" src="/image/browsers/opera.jpg" className={classes.browserImg}/>}
                    </div>
                    <span className={classes.browserName}>Opera</span>
                </div>
                <div className={classNames(classes.browserLine)}>
                    <div className={classNames(useLogos ? classes.browserImgCont : classes.noLogo)}>
                        { useLogos && <img alt="" src="/image/browsers/safari.jpg" className={classes.browserImg}/>}
                    </div>
                    <span className={classes.browserName}>Safari</span>
                </div>
                <div className={classNames(classes.browserLine)}>
                    <div className={classNames(useLogos ? classes.browserImgCont : classes.noLogo)}>
                        { useLogos && <img alt="" src="/image/browsers/edge.jpg" className={classes.browserImg}/>}
                    </div>
                    <span className={classes.browserName}>Edge</span>
                </div>
            </div>
        </div>
    }
}

export default withStyles(styles)(BrowserList);
