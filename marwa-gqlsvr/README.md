# linq
This project contains a client and server subfolder.

server - Node.js Express GraphQL server

client - React/ApolloClient app with development web server.

## Background
This project is mostly based on Lynda.com's
[Learning Apollo](https://www.lynda.com/GraphQL-tutorials/Learning-Apollo/614313-2.html)
video class and its project exercise code files for
'crm' project: (C:\code-reference\react\lynda\crm).

Upgraded for Apollo 2.1 instead of using Relay.

No need for updateSchema since now handled by Apollo makeExecutableSchema.

### GraphQL server
linq-server

Uses Node.js Express.

NOTE: In the future, my GraphQL server may interface with a MongoDB database server.

### React/Apollo app development web server
linq-client


## Install node_modules
```
yarn
OR
yarn install --production
```

## Run
Start local servers (GraphQL and React apps):
### Development
```
cd server
yarn              (installs node_modules devDependencies)
yarn start-dev

cd client
yarn              (installs node_modules devDependencies)
yarn start
```
Server App: GraphQL server: http://localhost:4000

Client App: React/Apollo app webpack development web server: http://localhost:3000

### Production
```
cd server
rm -R node_modules
yarn install --production  (force production environment, ignoring NODE_ENV, so no node_modules devDependencies)
yarn build                 (automatically calls 'prebuild')
yarn serve

cd client
yarn build
# Deploy: SFTP contents of build directory to production web/app server (e.g. NGINX or Apache2).
# NOTE: For linq-client, the production web server will automatically serve this.
```
Server App: GraphQL server: http://70.166.80.94:4000  (YODA)

Client App: React/Apollo app webpack development web server: http://70.166.80.94:3000  (YODA)


### Configuration
The server app's port number is controlled by these configuration settings:
* server/.env: PORT
* server/src/config.js: DEFAULT_PORT


## Developing
Any changes you make to files in these directories will
cause the Node.js to automatically rebuild the app:
* `server/src/`
* `client/src/` (Note: the browser will also automatically refresh)


# FUTURE: ================

### MongoDB database server
Back-end MongoDB database server that has a single 'user' collection.
* Uses `mongoose` NPM package to define the database schema.

Start database server:
```
Run script
Bash:  `./start-mongodb.bat`
Windows: `start-mongodb.bat`
```


# TODO: UPDATE THIS
## References
* Facebook's [Relay Modern](https://facebook.github.io/relay/)
* Facebook's [TodoMVC reference project](https://github.com/relayjs/relay-examples/tree/master/todo).
* Lynda.com - GraphQL: Data Fetching with Relay (Modern), React Project: friends
* OneNotes:
    * Facebook TodoMVC
    * GraphQL: Data Fetching with Relay
    * GraphQL/Database Server
    * mystarter-express-babel
* graphql/server - Fullstack React book's backend GraphQL server with NodeJS.
    * Book Reference: Part II: GraphQL Server (p.603)
    * Project code: `C:\dev\react\TRAINING\fullstack-react-code\graphql\server`
* relay/bookstore (ejected) - Fullstack React book's client-server web app using Relay Classic.
    * Book Reference: Part II: Relay (p.658)
    * Project code: `C:\dev\react\TRAINING\fullstack-react-code\relay\bookstore`
* `mystarter-express-babel` Starter Kit project.
