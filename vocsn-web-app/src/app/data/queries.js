/*
GraphQL queries for Apollo Client.
Use Apollo's gql function to wrap GraphQL query strings.
 */
import gql from 'graphql-tag';

import { ApolloClient } from 'apollo-client';
import { InMemoryCache } from 'apollo-cache-inmemory';
import { onError } from 'apollo-link-error';
import { ApolloLink } from 'apollo-link';

import { GQL_HOST } from '../config';
import Viewer from './Viewer';

const TAG = 'queries';


const GET_VIEWER = gql`
  query ViewerQuery($username: String!, $password: String!) {
    viewer(username: $username, password: $password) {
      username
      avatarImage
      viewerFacilities {
        facilityId
        facilityName
        facilityRiskFactorOptions {
          id
          name
        }
        viewerGroups {
          groupId
          groupName
          roleId
        }
      }      
    }
  }
`;


/**
 * Authenticate user by querying DB with username/password. If resource exists, then return Viewer object with user with
 * facility/group/role info.
 * IMPORTANT: With HTTPS, everything is encrypted (especially the username & password) before sending to GraphQL server!
 *
 * Fetch 'Viewer' GraphQL data, including user, facilities, groups, and riskfactors.
 * We do this by sending ApolloClient query with plain JavaScript.
 *
 * @param usr - username
 * @param pwd - password
 * @returns {Promise<*>} Resolves with Viewer object if successful user authentication, else throws error.
 * @throws Network error, or GraphQL error (specified resource does not exist), etc.
 */
export const authenticateViewer = async (usr, pwd) => {
  // Fetch 'Viewer' GraphQL data
  console.log(TAG, ': ApolloClient querying ', GQL_HOST); // ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

  // TODO: 8/15/2018 May want to access existing client using withApollo() or graphql()
  // NOTE: If you want to get direct access to your ApolloClient instance that is provided by <ApolloProvider/> in your
  // components, then be sure to look at the withApollo() enhancer function, which will create a new component which
  // passes in an instance of ApolloClient as a 'client' prop.
  // If you are wondering when to use withApollo() and when to use graphql(), the answer is that most of the time you
  // will want to use graphql().
  // Ref: withApollo - https://www.apollographql.com/docs/react/api/react-apollo.html#withApollo
  // Ref: graphql() -  https://www.apollographql.com/docs/react/api/react-apollo.html#graphql
  // const client = new ApolloClient({ uri: GQL_HOST }); // Access client directly using plain JavaScript
  const { createUploadLink } = require('apollo-upload-client');
  const client = new ApolloClient({
    link: ApolloLink.from([
      onError(({ graphQLErrors, networkError }) => {
        if (graphQLErrors)
          graphQLErrors.forEach(({ message, locations, path }) =>
              console.log(
                  `[GraphQL error]: Message: ${message}, Location: ${locations}, Path: ${path}`,
              ),
          );
        if (networkError) console.log(`[Network error]: ${networkError}`);
      }),
      new createUploadLink({
        uri: GQL_HOST,
        credentials: 'same-origin'
      })
    ]),
    cache: new InMemoryCache()
  });

  const { data } = await client.query({
    query: GET_VIEWER,
    variables: { username: usr, password: pwd },
  });
  // NOTE: ApolloClient.query() rejects with (throws) an error if user not found (bad logon). For example:
  // [GraphQL error]: Message: The specified resource does not exist.
  // RequestId:638259f0-4002-0064-4a6a-ec81c3000000
  // Time:2018-05-15T16:31:13.4539120Z, Location: [object Object], Path: user

  //
  // NOTE: IF WE GOT HERE, THEN ApolloClient DIDN'T THROW AN ERROR, SO USER IS AUTHENTICATED (FOUND)
  //
  const { viewer } = data;

  // User is authenticated (found), so create Viewer object for UI
  console.log(TAG, ': Viewer query successful!'); // ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
  return new Viewer(viewer);
  // Note: This return value (of an async function) is implicitly wrapped in Promise.resolve
};


export const GET_SESSION = gql`
    query getSession($sessionID: String!, $accessKey: String!) {
        getSession(sessionID: $sessionID, accessKey: $accessKey) {
            sessionID
            accessKey
            expireDT
        }
    }
`;

export const UPLOAD_FILE = gql`
    mutation singleUpload($sessionID: String!, $file: gqlUpload!, $sections: String!, $start: Int!, $end: Int!, 
        $hours: Int!, $size: Int!, $sn: String!, $exportDate: Int!, $uploadDate: Int!, $label: String) {
        singleUpload(sessionID: $sessionID, file: $file, sections: $sections, start: $start, end: $end, hours: $hours, 
            size: $size, sn: $sn, exportDate: $exportDate, uploadDate: $uploadDate, label: $label) {
            reportID
            status
        }
    }
`;

export const SET_STATUS = gql`
    mutation setStatus($sessionID: String!, $accessKey: String!, $snList: [String], $reportIdList: [String], $statusList: [Int]) {
        setStatus(sessionID: $sessionID, accessKey: $accessKey, snList: $snList, reportIdList: $reportIdList, statusList: $statusList)
    }
`;

export const DOWNLOAD_FILE = gql`
    query reportDownload($session: String!, $accessKey: String! $sn: String!, $reportID: String!) {
        reportDownload(session: $session, accessKey: $accessKey, sn: $sn, reportID: $reportID)
    }
`;

export const REPORT_STATUS = gql`
    query reportStatus($snList: [String], $reportIdList: [String]) {
        reportStatus(snList: $snList, reportIdList: $reportIdList) {
            reportID
            status
            errorLevel
        }
    }
`;

export const RECALL_REPORTS = gql`
    query recallReports($sessionID: String!, $accessKey: String!, $snList: [String], $reportIdList: [String]) {
        recallReports(sessionID: $sessionID, accessKey: $accessKey, snList: $snList, reportIdList: $reportIdList) {
            reportID
            sn
            reportType
            reportHours
            reportStart
            reportEnd
            exportDate
            sections
            status
            label
            uri
            errorLevel
        }
    }
`;

export const BATCH_REQUEST = gql`
    query batchRequest($sessionID: String!, $accessKey: String!, $snList: [String], $reportIdList: [String], $requestDT: Int!) {
        batchRequest(sessionID: $sessionID, accessKey: $accessKey, snList: $snList, reportIdList: $reportIdList, requestDT: $requestDT)
    }
`;

export const BATCH_DOWNLOAD = gql`
    query batchDownload($sessionID: String!, $accessKey: String!, $batchID: String!) {
        batchDownload(sessionID: $sessionID, accessKey: $accessKey, batchID: $batchID) {
            status
            progress
            URI
            message
        }
    }
`;

export const SEND_EMAIL = gql`
    query sendEmail($sessionID: String!, $accessKey: String!, $recordID: String!, $fromName: String!, $subject: String!, $toAddress: [String]!, 
        $link: String!, $fileName: String!, $sendDate: Float!, $multiple: Boolean!, $sn: String) {
        sendEmail(sessionID: $sessionID, accessKey: $accessKey, recordID: $recordID, fromName: $fromName, subject: $subject, toAddress: $toAddress, 
            link: $link, fileName: $fileName, sendDate: $sendDate, multiple: $multiple, sn: $sn)
    }
`;