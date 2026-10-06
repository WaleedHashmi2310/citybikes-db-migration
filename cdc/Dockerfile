FROM quay.io/debezium/connect:2.4

# The confluent-hub tool might not be in quay.io/debezium/connect, so we download the plugin manually
USER root
RUN yum install -y unzip wget || apt-get update && apt-get install -y unzip wget || microdnf install -y unzip wget

RUN wget https://hub-downloads.confluent.io/api/plugins/confluentinc/kafka-connect-s3/versions/10.5.15/confluentinc-kafka-connect-s3-10.5.15.zip -O /tmp/kafka-connect-s3.zip && \
    unzip /tmp/kafka-connect-s3.zip -d /kafka/connect/ && \
    rm /tmp/kafka-connect-s3.zip

USER kafka
