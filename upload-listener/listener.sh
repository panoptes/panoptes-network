#!/bin/bash

# Start the Cloud SQL Proxy
echo "Starting Cloud SQL Proxy"
/app/cloud_sql_proxy -instances=panoptes-survey:us-central1:panoptes-meta=tcp:5432 &

# Start the listener
echo "Staring listener script"
/opt/conda/bin/python3 /app/upload-listener/upload_listener.py