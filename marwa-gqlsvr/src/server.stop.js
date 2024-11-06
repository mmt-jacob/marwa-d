const io = require('socket.io-client');
const socketClient = io.connect('http://localhost:1900'); // Specify port if your express server is not using default port 80

socketClient.on('connect', () => {
    socketClient.emit('gqlServerStop');
    setTimeout(() => {
        process.exit(0);
    }, 1000);
});