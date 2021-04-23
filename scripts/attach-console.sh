#!/bin/sh
#
# Create tmux sessions and launch alarm services
# Author: Jacqueline Garrahan
#
# Copyright @2021 SLAC National Accelerator Laboratory
#


if [ "$1" == "-h" ]; then
  echo "Usage: create-window.sh config_name"
  exit 0
fi

if [[ -z "$1" ]]; then
  echo "Configuration name not provided."
  echo "Usage: create-window.sh config_name"
  exit 0
fi

config_name=$1

if [[ $( tmux list-windows -t nalms 2>/dev/null | grep $config_name ) ]] ; then
    tmux $TMUX_OPTS attach -t nalms
    tmux select-window -t nalms:$config_name
else 
    echo "No tmux window found for $config_name."
fi
