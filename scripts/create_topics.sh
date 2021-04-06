#!/bin/sh
#
# This script creates Kafka topics associated with a given configuration. 
#
# Copyright @2021 SLAC National Accelerator Laboratory

if [ $# -ne 1 ]
then
    echo "Usage: create_alarm_topics.sh Accelerator"
    exit 1
fi

config=$1

if [[ -d $KAFKA_TOP ]]; then 
    # Create the compacted topics.
    $KAFKA_TOP/bin/kafka-topics.sh  --bootstrap-server localhost:9092 --create --replication-factor 1 --partitions 1 --topic $config || 
    $KAFKA_TOP/bin/kafka-configs.sh --bootstrap-server localhost:9092 --entity-type topics --alter --entity-name $config \
            --add-config cleanup.policy=compact,segment.ms=10000,min.cleanable.dirty.ratio=0.01,min.compaction.lag.ms=1000

    # Create the command and talk topics
    for topic in "${config}Command" "${config}Talk"
    do
        $KAFKA_TOP/bin/kafka-topics.sh  --bootstrap-server localhost:9092 --create --replication-factor 1 --partitions 1 --topic $topic
        $KAFKA_PATH/bin/kafka-configs.sh --bootstrap-server localhost:9092 --entity-type topics --alter --entity-name $topic \
           --add-config cleanup.policy=delete,segment.ms=10000,min.cleanable.dirty.ratio=0.01,min.compaction.lag.ms=1000,retention.ms=20000,delete.retention.ms=1000,file.delete.delay.ms=1000
    done
else
    echo "Kafka path not found. Has environment been set? KAFKA_TOP: ${KAFKA_TOP}"
fi