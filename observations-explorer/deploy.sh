#!/bin/bash -e

npm run build
gsutil rsync -R dist gs://www.panoptes-data.net/
gsutil acl ch -u AllUsers:R -r gs://www.panoptes-data.net/