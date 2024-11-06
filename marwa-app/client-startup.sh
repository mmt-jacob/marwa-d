#!/usr/bin/env bash

######################################
##                                  ##
##     Report System                ##
##     React Client Prod Startup    ##
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
foundLastClient=false
lastDB="1"
lastClient="2"
newFile=""
while read line; do
  while IFS='=' read -ra ADDR; do
    for i in "${ADDR[@]}"; do
      if [ "$foundLastDB" = true ]
      then
        lastDB="$i"
      fi
      if [ "$foundLastClient" = true ]
      then
        lastClient="$i"
      fi
      front=${i:0:11}
      if [ "$front" = "LAST_DB_UPD" ]
      then
        foundLastDB=true
      fi
      if [ "$front" = "LAST_CLIENT" ]
      then
        foundLastClient=true
      fi
    done
    if [ "$foundLastClient" != true ]
    then
      newFile="$newFile$line"$'\n'
    else
      newFile="$newFile""LAST_CLIENT_BUILD =$lastDB"$'\n'
    fi
    foundLastDB=false
    foundLastClient=false
  done <<< "$line"
done < $filename

# Configuration change
if [ "$lastDB" != "$lastClient" ]
then
  echo "Configuration changed"
else
  echo "Configuration not changed"
fi

# If needed, rebuild
if { [ "$lastDB" != "$lastClient" ] && [ "$force" != true ]; } || { [ "$lastDB" = "$lastClient" ] && [ "$force" = true ]; }
then

  # Build node dependencies and compile code
  echo "Rebuilding client"
  yarn build
  cd build
  cp * /var/www/vocsn.com/ -r

  # Mark update times in environment configuration file
  echo "$newFile" > '../../.env.conf'

fi

# Start NGINX server
if [ "$force" != true ]
then
	echo "Starting Multi-View React Web App - Production"
	if systemctl is-active --quiet nginx
	then
		echo "Reloading NGINX Server"
		nginx -s reload
	else
		echo "Starting NGINX Service"
		service nginx start
	fi
fi
echo "Client reload complete"
