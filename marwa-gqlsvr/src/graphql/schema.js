/**
 * GraphQL schema
 * GraphQL needs a schema to understand what type of data is passed when we're making queries,
 * or when we're creating new types of data.
 *
 * Here we're using the graphql-tools package to create a GraphQL.js GraphQLSchema instance
 * from "GraphQL schema language" using the function makeExecutableSchema.
 *
 * Refs:
 * http://graphql.org/learn/schema/
 * https://www.apollographql.com/docs/graphql-tools/generate-schema.html
 *
 * Since we're using graphql-tools, the approach is:
 * 1) Describe the schema as a GraphQL type language string (i.e. typeDefs).
 * 2) Define resolvers as a nested object that maps type and field names to resolver functions.
 * 3) Combine the schema and resolvers using makeExecutableSchema().
 *
 * During development, we can temporarily provide mock functionality with addMockFunctionsToSchema()
 * until the GraphQL server provides real data.
 */
// TODO: 4/15/2018 Possibly limit User fields exposed here? Only those that are necessary?
// TODO: 4/14/2018 Break up into separate madules if gets too large, etc? - see:
//   https://www.apollographql.com/docs/graphql-tools/generate-schema.html#modularizing

import { makeExecutableSchema /* , addMockFunctionsToSchema */ } from 'graphql-tools';
import resolvers from './resolvers';
import { gql } from 'apollo-server-express';
// import resolvers from './data/mockJsonMem/resolvers';

// This loads the Upload type.
// const { ApolloServer, gql } = require('apollo-server-express');
// const { gql } = require('apollo-server-express');

// For Apollo, describe the schema as a GraphQL type definition language string:
export const typeDefs = gql`
  type Facility {
    id: ID!
    timestamp: String
    facilityId: String!
    name: String!
    shortName: String!
    address1: String!
    address2: String
    city: String!
    state: String!
    zip: String!
    country: String
    contactName: String!
    contactPhone: String
    contactEmail: String
    riskFactorOptions: [RiskFactor]
    groups: [Group]
  }
  
  type Group {
    groupId: String!
    name: String!
    description: String    
  }
  
  type RiskFactor {
    id: Int!
    name: String!
  }
  
  type User {
    id: ID!
    timestamp: String
    username: String!
    password: String!
    firstName: String
    lastName: String
    phone: String
    avatarImage: String
    facilityGroups: [FacilityGroup]
 }
  
  type FacilityGroup {
    facilityId: String!
    groups: [GroupRole]
  }
   
  type GroupRole { 
    groupId: String
    roleId: Int!
  }
  
  type Viewer {
    username: String!
    password: String!
    firstName: String
    lastName: String
    phone: String
    avatarImage: String
    viewerFacilities: [ViewerFacility]
 }
  
  type ViewerFacility {
    facilityId: String!
    facilityName: String!
    facilityRiskFactorOptions: [RiskFactor]
    viewerGroups: [ViewerGroupRole]
  }
  
  type ViewerGroupRole {
    groupId: String!
    groupName: String!
    roleId: Int!
  }
  
  type UserRole {
    id: ID!
    timestamp: String
    roleId: String!
    roleName: String!
    description: String
  }
  
  type RoomConfig {
    id: ID!
    timestamp: String
    facilityId: String! 
    groupId: String
    roomId: String!
    language: String 
    silence: String
    volume: String
    period: String
    frequency: String
    airBedSensitivity: String
    patientId: String
    patientNickname: String 
    patientRiskLevel: String
    patientRiskFactorIds: [Int]
    editedBy: String
    monitorType: String
    monitorSerial: String
    initialAlarm: String
    cmsSound: String
  }
  
  input RoomConfigInput {
    language: String
    silence: String
    volume: String
    period: String
    frequency: String
    airBedSensitivity: String
    patientId: String
    patientNickname: String 
    patientRiskLevel: String
    patientRiskFactorIds: [Int]
    editedBy: String
  }

  type EventNote {
    id: ID!
    eventId: Int!
    eventTimestamp: Int!
    eventLocation: String!
    eventType: String!
    eventNote: String!
  }

  type ReportStatus {
    reportID: String!
    status: Int!
    errorLevel: Int!
  }
  
  scalar gqlUpload

  type Session {
    sessionID: String
    accessKey: String
    expireDT: Int
  }

  type SessionReport {
    reportID: String
    sn: String
    reportType: String
    reportHours: Int
    reportStart: Int
    reportEnd: Int
    exportDate: Int
    sections: String
    status: Int
    label: String
    uri: String
    errorLevel: Int
  }
  
  type FileUpload {
    reportID: String!
    accessKey: String!
    status: String!
  }

  type BatchStatus {
      status: Int!
      progress: Float!
      URI: String!
      message: String!
  }

  type FileDownload {
    uri: String
  }
  
  type Query {
    viewer(username: String!, password: String!): Viewer
    user(username: String!, password: String!): User
    userRoles: [UserRole]
    facilitiesAll: [Facility]
    facilities(facilityIds: [String]!): [Facility]
    facility(facilityId: String!): Facility
    riskFactors(facilityId: String!): [RiskFactor]
    roomConfigs(facilityId: String!, groupId: String!): [RoomConfig]
    roomConfig(facilityId: String!, groupId: String!, roomId: String!): RoomConfig
    eventNotes(facilityId: String!): [EventNote]

    getSession(sessionID: String!, accessKey: String!): Session
    reportStatus(snList: [String], reportIdList: [String]): [ReportStatus]
    recallReports(sessionID: String!, accessKey: String!, snList: [String], reportIdList: [String]): [SessionReport]
    reportDownload(session: String!, accessKey: String!, sn: String!, reportID: String!): String
    batchRequest(sessionID: String!, accessKey: String!, snList: [String], reportIdList: [String], requestDT: Int!): String
    batchDownload(sessionID: String!, accessKey: String!, batchID: String!): BatchStatus
    sendEmail(sessionID: String!, accessKey: String!, recordID: String!, fromName: String!, subject: String!, toAddress: [String]!,
      link: String!, fileName: String!, sendDate: Float!, multiple: Boolean!, sn: String): [String]
    uploads: [FileUpload]
  }

  type Mutation {
    updateRoomConfig(facilityId: String!, groupId: String!, roomId: String!, config: RoomConfigInput!): RoomConfig
    singleUpload(sessionID: String!, file: gqlUpload!, sections: String!, start: Int!, end: Int!, hours: Int!, 
        size: Int!, sn: String!, exportDate: Int!, uploadDate: Int!, label: String): FileUpload!
    setStatus(sessionID: String!, accessKey: String!, snList: [String], reportIdList: [String], statusList: [Int]): Boolean
  }
`;

/* =============================
POSSIBILITIES/OBSOLETE: typeDef, Query, and Mutation

type UserFacility {
  id: ID!
    timestamp: String
  username: String!
    facilityId: String!
    groupId: String!
    userRoleId: Int!
}

type Query {
  groups(facilityId: String!): [Group]
  users: [User]
  viewer(username: String!, password: String!): String
  userFacilities(username: String!): [UserFacility]
}

type Mutation {
  addContact(id: String!, firstName: String!, lastName: String!): Contact
  addNote(note: NoteInput!): Note
}

type Subscription {
  noteAdded(contactId: ID!): Note
}
============================= */

// Combine the schema and resolvers:
// Ref: https://www.apollographql.com/docs/graphql-tools/generate-schema.html#makeExecutableSchema
const schema = makeExecutableSchema({ typeDefs, resolvers });

// Temporarily provide mock functionality, then comment-out when GraphQL server provides real data.
// NOTE: Uses 'Hello World' as the mock data for any String field.
// NOTE: If you are using mocking, the preserveResolvers argument of addMockFunctionsToSchema must
// be set to true if you do not want your resolvers to be overwritten by mock resolvers.
// Ref: https://www.apollographql.com/docs/graphql-tools/mocking.html#addMockFunctionsToSchema
// // addMockFunctionsToSchema({ schema });
// addMockFunctionsToSchema({ schema, preserveResolvers: true, });

export default schema;
