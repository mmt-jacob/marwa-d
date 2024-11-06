import 'babel-polyfill';
import React from 'react';
import ReactDOM from 'react-dom';
import './index.css';

// ////////////////// Choose which App to use:
import App from './app/App'; // LinQ App - NOTE: Requires our GraphQL server running.
import AppMaintenance from './app/AppMaintenance'; // Maintenance Page
// import App from './app_crm/App'; // NOTE: Requires our GraphQL server-crm running.
// import App from './app_apollo_getting_started/App'; // NOTE: Uses external GraphQL server.
// //////////////////

// TODO: 5/31/2018 Bring back registerServiceWorker? Or does NGINX already provide this, etc?
// NOTE: Commented-out due to Chrome browser error when running in production
// Error during service worker registration: DOMException: Only secure origins are allowed (see: https://goo.gl/Y0ZkNV)
// (anonymous) @ registerServiceWorker.js:80
// import registerServiceWorker from './registerServiceWorker';

const maintenanceMode = process.env.REACT_APP_MAINTENANCE_MODE === 'true';
if (maintenanceMode) {
  ReactDOM.render(<AppMaintenance />, document.getElementById('root'));
} else {
  ReactDOM.render(<App />, document.getElementById('root'));
}
// registerServiceWorker();


// //////////////////////
// APPROACH: Send query with plain JavaScript (My GraphQL Server)
//
// import ApolloClient from "apollo-boost";
// import gql from "graphql-tag";
//
// const PORT = 4000;
//
// const client = new ApolloClient({
//   uri: `http://localhost:${PORT}/graphql`
// });
//
// client.query({
//   query: gql`
//       {
//           contacts {
//               id
//               firstName
//               lastName
//           }
//       }
//   `
// })
// .then(result => console.log(result));
// //////////////////////

// //////////////////////
// APPROACH: Send query with plain JavaScript (Apollo:Getting Started)
// Ref: https://www.apollographql.com/docs/react/essentials/get-started.html
//
// import ApolloClient from "apollo-boost";
// import gql from "graphql-tag";
//
// const client = new ApolloClient({
//   uri: "https://w5xlvm3vzz.lp.gql.zone/graphql"
// });
// client.query({
//   query: gql`
//       {
//           rates(currency: "USD") {
//               currency
//           }
//       }
//   `
// })
// .then(result => console.log(result));
// //////////////////////
