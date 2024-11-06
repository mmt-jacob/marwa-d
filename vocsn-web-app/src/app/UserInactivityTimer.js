import { INACTIVITY_MS_INTERVAL, INACTIVITY_SHOWDIALOG, INACTIVITY_LOGOUT } from './config';

// TODO: 6/7/2018 Test in other web browsers on PC and on Phone, and on Meg's Mac (Safari)
// TODO: https://developer.mozilla.org/en-US/docs/Web/API/WindowOrWorkerGlobalScope/setInterval
// TODO: Enhancement: Encapsulate user activity in Render Prop or HOC? See https://reactjs.org/docs/render-props.html
/**
 * User Inactivity Timer
 * Maintain a timer to measure user-inactivity time (no mouse movements or key presses).
 * This is used to automatically logout the user when the user is inactive for a defined period of time.
 *
 * This utilizes plain-vanilla JavaScript to handle idle timeouts in a clean and self-contained manner.
 * With this implementation, the UI remains extremely responsive due to a very fast 'inactivityTimerReset' function tied
 * to the mouse & keyboard events.
 * Ref: https://stackoverflow.com/questions/667555/detecting-idle-time-in-javascript-elegantly/34516735#34516735
 */
const TAG = 'UserInactivityTimer:';

class UserInactivityTimer {
  constructor(extendSession) {
    this.intervalID = null;
    this.idleCounter = 0;
    this.server_expire = 1000;  // Placeholder until calculated
    this.extendSession = extendSession;
  }

  reset = () => {
    if (this.intervalID) {
      this.idleCounter = 0;
      // console.log(TAG, 'Reset inactivity timer');
    }
  };

  stop = () => {
    if (this.intervalID) {
      clearInterval(this.intervalID); // Stop this interval timer
      this.intervalID = null;
      // console.log(TAG, '** Stopped inactivity timer');

      // -------------------------------------------
      // document.onmousemove = null;
      // document.onkeypress = null;
      // Alternate approach - does it work?
      // document.removeEventListener('onmousemove', inactivityTimerReset);
      // document.removeEventListener('onkeypress', inactivityTimerReset);
      // -------------------------------------------
    }
  };

  start = (openDialog, doSomething) => {
    const INTERVAL_MS = INACTIVITY_MS_INTERVAL;
    const SHOWDIALOG_COUNT = INACTIVITY_SHOWDIALOG; // Number of intervals before showing dialog
    const DOSOMETHING_COUNT = INACTIVITY_LOGOUT; // Number of intervals before doing-something
    this.server_expire = SHOWDIALOG_COUNT;

    // -------------------------------------------
    // NOTE: When using React you should generally not need to call addEventListener to add listeners to a DOM element
    // after it is created. Instead, just provide a listener when the element is initially rendered.
    // Handling Events: https://reactjs.org/docs/handling-events.html
    // SyntheticEvent:  https://reactjs.org/docs/events.html#mouse-events
    // Render Props:    https://reactjs.org/docs/render-props.html
    //
    // document.onmousemove = inactivityTimerReset;
    // document.onkeypress = inactivityTimerReset;
    // Alternate approach - does it work?
    // document.addEventListener('onmousemove', inactivityTimerReset, true);
    // document.addEventListener('onkeypress', inactivityTimerReset, true);
    // -------------------------------------------

    // Repeatedly call the given function with a fixed time delay (ms) between each call
    this.intervalID = window.setInterval(() => {
      this.idleCounter += 1; // Count another delay interval (1 min if INTERVAL_MS=60000, or 1 sec if INTERVAL_MS=1000)
      this.server_expire -= 1;
      // console.log(TAG, 'countdown =', DOSOMETHING_COUNT - this.idleCounter);

      // Reset server expiration date before it expires if there was new activity
      if (this.idleCounter < SHOWDIALOG_COUNT && this.server_expire <= 0) {
        // console.log("Extending session");
        this.extendSession();
        this.server_expire = SHOWDIALOG_COUNT;
      }

      // If we reached the count to execute the 'openDialog' callback -- call only once!
      // (e.g. show warning dialog that user is almost out-of-time)
      if (this.idleCounter === SHOWDIALOG_COUNT) {
        // Estimate time when 'doSomething' callback will be executed
        const timestampRemaining = INTERVAL_MS * (DOSOMETHING_COUNT - SHOWDIALOG_COUNT);
        const timestampExpired = Date.now() + timestampRemaining;
        const expirationDate = new Date(timestampExpired);
        openDialog(expirationDate);
      } else if (this.idleCounter >= DOSOMETHING_COUNT) {
        // User is out-of-time, so do something (i.e. log user out)
        console.log(TAG, 'Session expired due to inactivity');
        this.stop();
        doSomething();
      }
    }, INTERVAL_MS);

    // console.log(TAG, 'Started inactivity timer');
    // console.log(TAG, 'countdown =', DOSOMETHING_COUNT - this.idleCounter);
  };
}

export default UserInactivityTimer;
