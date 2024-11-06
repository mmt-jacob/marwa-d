# LinQ application

Twin Oaks Technologies "LinQ" consists of a client app that is a
single-page web app using Material-UI framework, and a GraphQL server app.

## Background
This project is for Twin Oaks Technologies and is mostly based on the
Lynda.com "Learning Apollo" video class bases its project exercise code files.

The project is divided into 2 applications in separate root subfolders:
* 'client' - A React/Apollo Client, single-page web app generated using
Create-React-App.
* 'server' - Node.js Express app with MongoDB/Mongoose database.

### GraphQL server
My GraphQL server that interfaces with MongoDB database server.
Uses Node.js Express.

### MongoDB database server
Back-end MongoDB database server that uses `mongoose` NPM package to
define the database schema.

Start database server:
```
Run script
Bash:  `./start-mongodb.bat`
Windows: `start-mongodb.bat`
```

## Install project dependencies
Unstall dependencies for both the client and server apps:
```
$ cd client
$ yarn

$ cd server
$ yarn
```

## Run
Start Express/GraphQL server and App development web server:

Set up generated files:
```
$ cd server
$ yarn start

$ cd client
$ yarn start
```

* React/Apollo app web server: http://localhost:3000
* GraphQL server: http://localhost:4000
* GraphiQL tool: http://localhost:4000/graphiql

## Developing
Any changes you make to files in the `src/` directory will cause the server to
automatically rebuild the app and refresh your browser.

## References
* Lynda.com
    * GraphQL: "Learning Apollo" by Emmanuel Henri, Released: 10/2/2017
        * README: client/src/app_crm/README.md
        * [Lynda.com URL](https://www.lynda.com/GraphQL-tutorials/Next-steps/614313/662829-4.html)
        * Project folder: C:\code-reference\react\lynda\crm
        * OneNote: "Lynda.com Learning Apollo"
    * React: "friends" project. See C:\code-reference\react\lynda\friends_keepnodemodules
* UI code:
    * [Component Demos Code](https://github.com/mui-org/material-ui/tree/v1-beta/docs/src/pages/demos)
    * [Material-UI Example Projects](https://material-ui-next.com/getting-started/example-projects/)
    * [Material-UI](onenote:///C:\Users\Mike\Documents\CloudStation\OneNote\CheatSheets\Development\React\Node%20Modules.one#Material-UI&section-id={6614524F-08FC-4864-B900-B8E9643A1F75}&page-id={5EE5839E-FD29-4B2C-ACC6-6A07B10448DC}&end)
* OneNotes:
    * "Lynda.com Learning Apollo"
    * GraphQL/Database Server
    * mystarter-express-babel
* graphql/server - Fullstack React book's backend GraphQL server with NodeJS.
    * Book Reference: Part II: GraphQL Server (p.603)
    * Project code: `C:\dev\react\TRAINING\fullstack-react-code\graphql\server`

### Relay References
* Facebook's [Relay Modern](https://facebook.github.io/relay/)
* Facebook's [TodoMVC reference project](https://github.com/relayjs/relay-examples/tree/master/todo).
* Lynda.com - GraphQL: Data Fetching with Relay (Modern), React Project: friends
* OneNotes:
    * Apollo
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
