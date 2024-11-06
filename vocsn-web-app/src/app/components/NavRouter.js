import React from 'react';
import PropTypes from 'prop-types';

import Home from '../pages/Home';
import Upload from '../pages/Upload';
import Reports from '../pages/Reports';
import {
  NAV_HOME,
  NAV_UPLOAD,
  NAV_ROOMCONFIG,
  NAV_REPORTS,
  NAV_REMOTEDISPLAY,
  NAV_SYSTEMCONFIG, NAV_EVENTNOTE,
} from '../data/ui_constants';

/**
 * My custom navigation router.
 * NOTE: Originally necessary only when Relay was used for the GraphQL implementation.
 *
 * NOTE: This is a Stateless Component:
 *  - Simply returns JSX elements. So no need for curly braces (either use parenthesis or none OK).
 *  - Accept 'props' function argument and de-structure it to only receive the specific props we need.
 * @param whichPage
 * @param viewer
 * @param rootRef
 * @returns {*}
 * @constructor
 */
const NavRouter = ({ whichPage, viewer, loginRef }) => {
  // /////////////////////
  // // TODO: 3/30/2018 Still need this logic?
  // if (facilityId === null) {
  //   return <Home />;
  // }
  // /////////////////////

  // const { facilityId } = viewer.currentFacility;
  // console.log('whichPage=', whichPage, ', facilityId=', facilityId);
  const facilityId = null; // TODO: 5/16/2018 Use viewer instead or use real facilityId

  switch (whichPage) {
    case NAV_HOME:
      return <Home loginRef={loginRef}/>;
    case NAV_UPLOAD:
      return <Upload viewer={viewer} />; // TODO: 5/17/2018 Likewise implement for other pages using viewer
    case NAV_REPORTS:
      return <Reports facilityId={facilityId} viewer={viewer}/>;
    default:
      return (
        <p>404 Unknown page requested</p> // TODO: Create real 404 error page
      );
  }
};

NavRouter.propTypes = {
  whichPage: PropTypes.string.isRequired,
  // facilityId: PropTypes.string,
  viewer: PropTypes.object,
};

// NavRouter.defaultProps = {
//   facilityId: null,
// };

export default NavRouter;
