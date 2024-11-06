import 'babel-polyfill';
const process = require('process');
import express from 'express';
const graphqlHTTP = require('express-graphql');
import { graphqlExpress, ApolloServer, gql } from 'apollo-server-express';
import { init_tables, init_file_shares } from './data/azure/db_init.js';
const fs = require('fs');

// import http from 'http'
// import cors from 'cors';
// import https from 'https'
// import bodyParser from 'body-parser';
// import { apolloUploadExpress } from 'graphql-upload';

// import logger from 'winston';
import { initLogger, logger } from './logger';
import { GQL_HOST, GQL_PORT, WHITELIST, SYS_VER, MOD_VER, isProdEnv } from './config';
import { typeDefs } from './graphql/schema';
import resolvers from './graphql/resolvers';
// import { apolloUploadExpress } from 'apollo-upload-server'


// Initialize Winston logger
initLogger();
// showConfigs(); // TODO: EVENTUALLY DELETE THESE LOG STATEMENTS IN PRODUCTION ENVIRONMENT!


// Listen for stop signal
if (isProdEnv()) {
    const http = require('http');
    const server = http.createServer(app);
    const io = require('socket.io')(server);
    const socPort = 1900;
    server.listen(socPort, () => {
        logger.info('Termination signal listening on port ' + socPort.toString());
    });
    io.on('connection', (socketServer) => {
        socketServer.on('gqlServerStop', () => {
            process.exit(0);
        });
    });
}


// Initialize server
logger.info('Initializing server...');
const apollo = new ApolloServer({
    typeDefs,
    resolvers,
    context: ({ req }) => {
        return { req };
    },
});

// Enable CORS to allow requests from our client app (web) server.
// Configure CORS w/ Dynamic Origin: https://www.npmjs.com/package/cors#configuring-cors-w-dynamic-origin
const corsOptions = {
  origin: (origin, callback) => {
    if (WHITELIST.indexOf(origin) !== -1) {
      callback(null, true);
    } else {
      // Skip warning message if origin is undefined
      if (origin) {
        logger.warn(`CORS blocked origin = '${origin}' - TechDuke does not allow this!`);
      }
      callback(null, false);
      // callback(new Error(`Not allowed by CORS: ${origin}`));
    }
  },
};
// server.use('*', cors(corsOptions));
// server.use('*', cors({ origin: CORS_URL_APP_SERVER }));
// server.use('*', cors()); // Simple Usage (Enable All CORS Requests)
// TODO: 4/14/2018 Add authentication - see:
// https://www.apollographql.com/docs/react/recipes/authentication.html#Header
// https://www.apollographql.com/docs/react/recipes/authentication.html#Cookie
//
// var corsOptions = {
//   origin: '<insert uri of front-end domain>',
//   credentials: true // <-- REQUIRED backend setting
// };
// app.use(cors(corsOptions));

// -----------------------------
// Set up GraphQL server (No Subscriptions)
const app = express();

// app.use('/graphql', function (req, res, next) {
//     logger.info(req);
//     logger.info(req.headers);
//     next()
// });

apollo.applyMiddleware(
    {
        app,
        path: '/graphql',
        cors: corsOptions,
        bodyParserConfig: true
    });

// Instantiate server
// let server;
// if (isProdEnv()) {
//     // Assumes certificates are in a .ssl folder off of the package root. Make sure
//     // these files are secured.
//     server = https.createServer(
//         {
//             key: fs.readFileSync(`./ssl/star_venteclife_com.key`),
//             cert: fs.readFileSync(`./ssl/star_venteclife_com.crt`)
//         },
//         app
//     )
// } else {
//     server = http.createServer(app)
// }


// server.use('/graphql', apolloUploadExpress({ maxFileSize: 10000000, maxFiles: 10 }));
// app.use('/graphql', graphqlHTTP(
//   req => ({
//     schema: myGraphQLSchema,
//     context: { req }
//   })));
// server.use('/graphql', graphqlExpress({ schema: myGraphQLSchema }));
// server.use('/graphql', bodyParser.json());
// server.use('/graphql', apolloUploadExpress({ maxFileSize: 10000000, maxFiles: 10 }), graphqlHTTP({ schema: myGraphQLSchema }));
// server.use('/graphql', bodyParser.json(), graphqlExpress({ schema: myGraphQLSchema }));
// server.use('/graphiql', bodyParser.json(), graphiqlExpress({ endpointURL: '/graphql' }));

// Enable multi-part body parsing for uploads
// server.use('/graphql', bodyParser.json());
// server.use('/graphql', graphqlConnect({ schema: myGraphQLSchema }));

// Startup messages
logger.info("VOCSN Multi-View Report System - v" + SYS_VER);
logger.info("VOCSN GraphQL Server - v" + MOD_VER);
logger.info(`Server starting in ${process.env.NODE_ENV} environment`);
logger.info(`Endpoint: ${GQL_HOST}`);

// Port listeners
app.listen({port: GQL_PORT}, () => {
  logger.info("---- GraphQL Server is online ----");
});

// Initialize database - Creates tables for the first time if needed
if (init_tables(logger))
{
  logger.info("All required tables found or created.");
} else {
  logger.error("Unable to verify or create required tables.");
  process.exit();
}
if (init_file_shares(logger) === true)
  logger.info("All required file shares found or created.");
else {
  logger.error("Unable to verify or create required file shares.");
  process.exit();
}