import 'babel-polyfill';
import {
  singleUpload,
  getSession,
  getReportStatus,
  getTempReportURI,
  getSessionReports,
  makeBatchRequest,
  getBatchDownload,
  sendEmail,
  setStatus
} from '../data/azure/dbAzure';

/**
 * Resolver Map - In order to respond to queries, a schema needs to have resolve functions for all fields.
 * Resolve functions cannot be included in the GraphQL schema language, so they must be added separately.
 * This collection of functions is called the “resolver map”.
 * Ref: https://www.apollographql.com/docs/graphql-tools/resolvers.html
 */

// TODO: 4/14/2018 For more info, read https://www.apollographql.com/docs/graphql-tools/resolvers.html
// Define Resolver Map ('resolvers') as a nested object that maps type and field names to resolver functions:
// Should have a map of resolvers for each relevant GraphQL Object Type.
// Every resolver in a GraphQL.js schema accepts four positional arguments:
//   fieldName(obj, args, context, info) { result }
const resolvers = {
  Query: {
    viewer: (obj, args) => getViewer(args.username, args.password),
    user: (obj, args) => getUser(args.username, args.password),

    reportStatus: (obj, { snList, reportIdList }) => getReportStatus(snList, reportIdList),
    recallReports: (obj, { sessionID, accessKey, snList, reportIdList }, ctx) => getSessionReports(ctx, sessionID, accessKey, snList, reportIdList),
    getSession: (obj, { sessionID, accessKey }, ctx) => getSession(ctx, sessionID, accessKey),

    reportDownload: (obj, { sessionID, accessKey, sn, reportID }, ctx) => getTempReportURI(ctx, sessionID, accessKey, sn, reportID),
    batchRequest: (obj, { sessionID, accessKey, snList, reportIdList, requestDT}, ctx) => makeBatchRequest(ctx, sessionID, accessKey, snList, reportIdList, requestDT),
    batchDownload: (obj, { sessionID, accessKey, batchID}, ctx) => getBatchDownload(ctx, sessionID, accessKey, batchID),
    sendEmail: (obj, { sessionID, accessKey, recordID, fromName, subject, toAddress, link, fileName, sendDate, multiple, sn}, ctx) =>
        sendEmail(ctx, sessionID, accessKey, recordID, fromName, subject, toAddress, link, fileName, sendDate, multiple, sn)
  },
  Mutation: {
    singleUpload: async (obj, {sessionID, file, sections, start, end, hours, size, sn, exportDate, uploadDate, label}, ctx) =>
        singleUpload(ctx, sessionID, file, sections, start, end, hours, size, sn, exportDate, uploadDate, label),
    setStatus: async (obj, {sessionID, accessKey, snList, reportIdList, statusList}, ctx) =>
        setStatus(ctx, sessionID, accessKey, snList, reportIdList, statusList)
  },
};

export default resolvers;
