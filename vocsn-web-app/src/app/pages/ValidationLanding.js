import React from 'react';
import { withApollo } from 'react-apollo';
import classNames from 'classnames';
import Button from '@material-ui/core/Button';
import { withStyles } from '@material-ui/core/styles';

const styles = theme => ({
    content: {
        width: '100%',
        height: 'calc(70% - 30%)',
        position: 'relative',
        margin: '0 auto',
        paddingTop: '30px',
        textAlign: 'center',
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
    message: {
        fontSize: '18px',
        fontFamily: '"avenir-heavy","Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif',
        marginBottom: '20px',
        textAlign: 'center',
        [theme.breakpoints.up('sm')]: {
            fontSize: '20px',
            marginTop: '50px',
        },
        [theme.breakpoints.up('lg')]: {
            fontSize: '24px',
            marginTop: '70px',
        },
    },
    orangeButton: {
        alignItems: 'center',
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
                backgroundColor: theme.palette.secondary.dark,
            },
        },
        '&:disabled': {
            color: theme.palette.disabled.light,
            backgroundColor: theme.palette.disabled.dark,
        }
    },
    enter: {
        margin: '0',
        fontSize: '28px',
        lineHeight: '48px',
        padding: '0px 30px',
        height: '48px',
        width: '130px',
        [theme.breakpoints.up('sm')]: {
            fontSize: '28px',
            padding: '0px 35px',
        },
        [theme.breakpoints.up('md')]: {
            fontSize: '28px',
            padding: '0px 35px',
        },
        [theme.breakpoints.up('lg')]: {
            fontSize: '32px',
            padding: '0px 40px',
        }
    },
});

class ValidationLanding extends React.Component {
    constructor(props) {
        super(props);
        this.enter = props.enter;
    };

    render() {
        const { classes } = this.props;
        return (
            <div>
                <div className={classes.content}>
                    <div className={classes.message} style={{marginTop: '25px', fontSize: '30px'}}>
                        Multi-View Reports V&V Portal
                    </div>
                    <Button className={classNames(classes.orangeButton, classes.enter)} tabIndex={-1}
                            onClick={() => (this.enter())}>
                        Enter
                    </Button>
                    <div className={classes.message} style={{margin: '10px', fontSize: '16px'}}>
                        By clicking “Enter” I agree to the VOCSN Multi-View&nbsp;
                        <a href="https://www.venteclife.com/page/privacy-policy">terms and conditions of use.</a>
                    </div>
                    <div className={classes.message} style={{marginTop: '20px', fontSize: '16px', color: 'red'}}>
                        Important: This site is intended for verification and validation purposes only. Do not use without authorization from Ventec Life Systems.
                    </div>
                </div>
            </div>
        );
    }
}

export default withStyles(styles, { withTheme: true })(withApollo(ValidationLanding));
