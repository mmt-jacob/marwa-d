/**
 * NOTE 1: The Lynda.com author claims we also need GraphQL schema file in client to make sure the types are checked before we send those queries to the server
 * But I don't see this ever being used in his project!
 *
 * NOTE: 2: On the server, Apollo uses a template string (typeDefs) to define the GraphQL type definition (graphql/schema.js)
 */
// export const typeDefs = `
//   type Contact {
//     id: ID!
//     firstName: String
//     lastName: String
//   }
//
//   type Query {
//     contacts: [Contact]
//   }
// `;
