#!/bin/sh
#
# Stops Kafka server 
#
# Copyright @2021 SLAC National Accelerator Laboratory

if [[ -d $KAFKA_TOP ]]; then 

    if _; then
        $KAFKA_TOP/bin/kafka-server-stop.sh

    else
        echo "No running Kafka brokers found."
    fi
else
    echo "Kafka path not found. Has environment been set? KAFKA_TOP: ${KAFKA_TOP}"
fi