#!/bin/bash -e

echo "Starting Cloud SQL proxy"
python3 /var/panoptes/PIAA/scripts/connect_cloud_sql_proxy.py --config /var/panoptes/PIAA/conf.yaml --verbose &

echo "Starting Flask solver"
gunicorn app:app -b 0.0.0.0:8000
