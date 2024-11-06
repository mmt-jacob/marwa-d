import React from 'react';
import { withApollo } from 'react-apollo';
import { withStyles } from '@material-ui/core/styles';

const styles = theme => ({
    content: {
        width: '100%',
        height: 'calc(70% - 30%)',
        position: 'relative',
        margin: '0 auto',
        paddingTop: '30px',
    },
    logo: {
        position: 'absolute',
        width: '160px',
        height: '64px',
        left: '7px',
        top: '-40px',
        [theme.breakpoints.up('md')]: {
            width: '190px',
            height: '76px',
            left: '22px',
            top: '-51px'
        },
        [theme.breakpoints.up('lg')]: {
            width: '240px',
            height: '96px',
            left: '25px',
            top: '-70px'
        },
        [theme.breakpoints.up('xl')]: {
            width: '280px',
            height: '112px',
            left: '31px',
            top: '-70px'
        }
    },
    expired: {
        fontSize: '18px',
        fontFamily: '"avenir-heavy","Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif',
        margin: 'auto',
        marginTop: '70px',
        padding: '30px',
        textAlign: 'center',
        [theme.breakpoints.up('sm')]: {
            fontSize: '20px',
            marginTop: '50px',
        },
        [theme.breakpoints.up('lg')]: {
            fontSize: '24px',
            marginTop: '70px',
        },
    }
});

class AppUnavailable extends React.Component {
    constructor(props) {
        super(props);
        this.message = props.message;
    };
    state = {};

    render() {
        const { classes } = this.props;
        return (
            <div>
                <div className={classes.content}>
                    <div className={classes.expired}>
                        { this.message }
                    </div>
                </div>
            </div>
        );
    }
}

export default withStyles(styles, { withTheme: true })(withApollo(AppUnavailable));
