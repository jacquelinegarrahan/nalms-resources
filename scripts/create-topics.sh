#!/bin/sh
#
# This script creates Kafka topics associated with a given configuration. 
# Author: Jacqueline Garrahan
#
# Copyright @2021 SLAC National Accelerator Laboratory

if [ $# -ne 1 ]
then
    echo "Usage: create_topics.sh Accelerator"
    exit 1
fi

if [[ ! -d "$KAFKA_TOP" ]]; then
  echo "KAFKA_TOP is not set."
  exit 0
fi

if [[ -z "$KAFKA_BOOTSTRAP" ]]; then
  echo "KAFKA_BOOTSTRAP server is not set."
  exit 0
fi


config=$1

if [[ -d $KAFKA_TOP ]]; then 
    # Create the compacted topics.
    $KAFKA_TOP/current/bin/kafka-topics.sh  --bootstrap-server $KAFKA_BOOTSTRAP --create --replication-factor 1 --partitions 1 --topic $config || 
    $KAFKA_TOP/current/bin/kafka-configs.sh --bootstrap-server $KAFKA_BOOTSTRAP --entity-type topics --alter --entity-name $config \
            --add-config cleanup.policy=compact,segment.ms=10000,min.cleanable.dirty.ratio=0.01,min.compaction.lag.ms=1000

    # Create the command and talk topics
    for topic in "${config}Command" "${config}Talk"
    do
        $KAFKA_TOP/current/bin/kafka-topics.sh  --bootstrap-server $KAFKA_BOOTSTRAP --create --replication-factor 1 --partitions 1 --topic $topic
        $KAFKA_TOP/current/bin/kafka-configs.sh --bootstrap-server $KAFKA_BOOTSTRAP --entity-type topics --alter --entity-name $topic \
           --add-config cleanup.policy=delete,segment.ms=10000,min.cleanable.dirty.ratio=0.01,min.compaction.lag.ms=1000,retention.ms=20000,delete.retention.ms=1000,file.delete.delay.ms=1000
    done
else
    echo "Kafka path not found. Has environment been set? KAFKA_TOP: ${KAFKA_TOP}"
fi