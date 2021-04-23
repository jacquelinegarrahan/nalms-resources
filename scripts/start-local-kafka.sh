#!/bin/sh
#
# Starts kafka server 
# Author: Jacqueline Garrahan
#
# Copyright @2021 SLAC National Accelerator Laboratory


if [ "$1" == "-h" ]; then
  echo "Usage: start_kafka.sh zookeeper_property_file server_property_file"
  exit 0
fi

# Check property file provided
if [[ -z "$1" ]]; then
  if [[-z "$ZOOKEEPER_PROPERTY_FILE"]]; then
    echo "Property files not provided. Must pass property files or define \$ZOOKEEPER_PROPERTY_FILE and \$SERVER_PROPERTY_FILE"
    echo "Usage: start_kafka.sh zookeeper_property_file server_property_file"
    exit 0
  fi
fi

if [[ -z "$2" ]]; then
  echo "Kafka server property files not provided."
  echo "Usage: start_kafka.sh zookeeper_property_file server_property_file"
  exit 0
fi

# check KAFKA_TOP is set
if [[ ! -d "$KAFKA_TOP" ]]; then
  echo "KAFKA_TOP is not set."
  exit 0
fi

# check NALMS_TOP is set
if [[ ! -d "$NALMS_TOP" ]]; then
  echo "KAFKA_TOP is not set."
  exit 0
fi

ZOOKEEPER_PROPERTY_FILE=$1
SERVER_PROPERTY_FILE=$2

ZOOKEEPER_HOST_BASE="$(cut -d':' -f1 <<< $ZOOKEEPER_HOST)"
ZOOKEEPER_PORT="$(cut -d':' -f2 <<< $ZOOKEEPER_HOST)"

if [[ -d "$KAFKA_TOP" ]]; then
    if [[ (( -f "$ZOOKEEPER_PROPERTY_FILE" && -f "$SERVER_PROPERTY_FILE" )) || -d "$NALMS_TOP" ]]; then
        if [[ -f "$ZOOKEEPER_PROPERTY_FILE" ]]; then
            $KAFKA_TOP/bin/zookeeper-server-start.sh  -daemon $ZOOKEEPER_PROPERTY_FILE
        else
            $KAFKA_TOP/bin/zookeeper-server-start.sh  -daemon $NALMS_TOP/config/local_zookeeper.properties
        fi
        echo "Starting Zookeeper..."

        # allow time to set up
        sleep 30

        # check zookeeper has started
        if [[ ! -z $( echo srvr | nc $ZOOKEEPER_HOST_BASE $ZOOKEEPER_PORT ) ]]; then
            echo "Starting Kafka cluster..."
            if [[ -f "$SERVER_PROPERTY_FILE" ]]; then
                $KAFKA_TOP/bin/kafka-server-start.sh  -daemon $SERVER_PROPERTY_FILE
            else
                $KAFKA_TOP/bin/kafka-server-start.sh  -daemon $NALMS_TOP/config/local_server.properties
            fi
        else
            echo "Running zookeeper not detected after 30 second timeout."
        fi
    else
        echo "Missing paths. Either NALMS_TOP or server property file and zookeeper property file must be defined."
        echo "Server property file: ${SERVER_PROPERTY_FILE}"
        echo "Zookeeper property file: ${ZOOKEEPER_PROPERTY_FILE}"
        echo "NALMS_TOP: ${NALMS_TOP}"
    fi
else
    echo "Kafka path not found. Has environment been set? KAFKA_TOP: ${KAFKA_TOP}"
fi
