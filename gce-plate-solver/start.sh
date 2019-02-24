#!/bin/bash -e

echo "Starting Cloud SQL proxy"
python3 /var/panoptes/PIAA/scripts/connect_cloud_sql_proxy.py --config /var/panoptes/PIAA/conf.yaml --verbose &

echo "Starting PubSub listener"
python3 pubsub-listener.py
