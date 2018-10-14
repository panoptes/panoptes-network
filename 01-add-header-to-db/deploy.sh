#!/bin/bash -e

gcloud functions deploy \
                 header-to-metadb \
                 --entry-point header_to_db \
                 --runtime python37 \
                 --trigger-http