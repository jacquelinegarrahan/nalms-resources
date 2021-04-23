#!/bin/sh
#
# Create tmux sessions and launch alarm services
#
# Copyright @2021 SLAC National Accelerator Laboratory

if [ "$1" == "-h" ]; then
  echo "Usage: create-window.sh config_name"
  exit 0
fi

if [[ -z "$1" ]]; then
  echo "Configuration name not provided."
  echo "Usage: create-window.sh config_name config_file"
  exit 0
fi

if [[ -z "$2" ]]; then
  echo "Configuration file not provided."
  echo "Usage: create-window.sh config_name config_file"
  exit 0
fi

export PATH="$JAVA_HOME/bin:$PATH"

CONFIG_NAME=$1
CONFIG_FILE=$2

# create nalms session if not running, attach otherwise
if [[ -z $(tmux list-sessions 2>/dev/null | grep nalms) ]]; then
  tmux $TMUX_OPTS new-session -s nalms -d
fi

# create config name
tmux new-window -a -t nalms -n $CONFIG_NAME -c $PWD

#create panes
tmux split-window -t nalms:$CONFIG_NAME
tmux select-layout -t nalms:$CONFIG_NAME tiled > /dev/null

SERVER_JAR=`echo "${NALMS_TOP}/alarm-server/current/service-alarm-server-*.jar"`
LOGGER_JAR=`echo "${NALMS_TOP}/alarm-logger/current/service-alarm-logger-*.jar"`
LOGGING_SETTINGS="${NALMS_TOP}/config/logging.properties"
ALARM_SERVER_SETTINGS="${NALMS_TOP}/config/alarm_server_settings.ini"

if java -jar $SERVER_JAR -logging $LOGGING_SETTINGS -config $CONFIG_NAME -import $CONFIG_FILE; then
  # set up server window 
  tmux send-keys -t nalms:$config_name.0 "java -jar $SERVER_JAR -config $CONFIG_NAME -logging $LOGGING_SETTINGS -settings $ALARM_SERVER_SETTINGS" C-m

  # set up logger window
  tmux send-keys -t nalms:$config_name.1 "java -jar $LOGGER_JAR -logging $LOGGING_SETTINGS -settings $ALARM_SERVER_SETTINGS " C-m

  #kill the first window
  tmux kill-window -t nalms:$( tmux list-windows -t nalms -F "#{window_index}" | head -n 1 )

  tmux $TMUX_OPTS attach-session -t nalms
else
    echo "Unable to import configuration."
fi
