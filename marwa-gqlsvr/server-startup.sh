#!/usr/bin/env bash

######################################
##                                  ##
##    Report System                 ##
##   GraphQL Server Prod. Startup   ##
##                                  ##
######################################

# Check if configuration is up to date
# If up to date, start serving
# If not up to date, rebuild, then serve

# Require root privileges
if [[ $(/usr/bin/id -u) -ne 0 ]]; then
    echo "Root permissions required."
    exit
fi

# Allow caller to force rebuild
force=false
if [ $1 = "force" ]
then
  force=true
  echo "Forcing rebuild"
fi

# Read last update times from environment configuration file.
echo "Checking for configuration changes"
filename='../.env.conf'
foundLastDB=false
foundLastServ=false
lastDB="1"
lastServ="2"
newFile=""
while read line; do
  while IFS='=' read -ra ADDR; do
    for i in "${ADDR[@]}"; do
      if [ "$foundLastDB" = true ]
      then
        lastDB="$i"
      fi
      if [ "$foundLastServ" = true ]
      then
        lastServ="$i"
      fi
      front=${i:0:11}
      if [ "$front" = "LAST_DB_UPD" ]
      then
        foundLastDB=true
      fi
      if [ "$front" = "LAST_SERVER" ]
      then
        foundLastServ=true
      fi
    done
    if [ "$foundLastServ" != true ]
    then
      newFile="$newFile$line"$'\n'
    else
      newFile="$newFile""LAST_SERVER_BUILD =$lastDB"$'\n'
    fi
    foundLastDB=false
    foundLastServ=false
  done <<< "$line"
done < $filename

# Configuration change
if [ "$lastDB" != "$lastServ" ]
then
  echo "Configuration changed"
else
  echo "Configuration not changed"
fi

# If needed, rebuild
if { [ "$lastDB" != "$lastServ" ] && [ "$force" != true ]; } || { [ "$lastDB" = "$lastServ" ] && [ "$force" = true ]; }
then

  # Build node dependencies and compile code
  echo "Rebuilding GraphQL Server"
  cd ~/marwa/server
  rm node_modules -r
  yarn install --production
  yarn build

  # Mark update times in environment configuration file
  echo "$newFile" > '../.env.conf'

fi

# Start server
if [ "$force" != true ]
then
  echo "Starting Multi-View GraphQL Server - Production"
  ../../.nvm/versions/node/v12.14.0/bin/node build/server.js
fi
