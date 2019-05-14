#!/bin/bash -e

echo "Starting Cloud SQL proxy"
python3 /var/panoptes/PIAA/scripts/connect_cloud_sql_proxy.py --config /var/panoptes/PIAA/conf.yaml --verbose &

echo "Getting astrometry.net files"
python3 $POCS/pocs/utils/data.py --wide-field --narrow-field

echo "Getting DB passwords from metadata server"
curl --silent "http://metadata.google.internal/computeMetadata/v1/project/attributes/pgpass" -H "Metadata-Flavor: Google" > $HOME/.pgpass
chmod 600 $HOME/.pgpass

# Execute remaining commands
exec "$@"
