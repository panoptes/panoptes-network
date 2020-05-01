Firestore Stats Updater
-----------------------

This folder defines some Cloud Functions that are automatically triggered 
any time `observations` or `images` firestore records are added or removed.

This is used as a simple aggregator, with results stored in the `stats` collection.

### Deploy

The `deploy.sh` script runs a series of `gcloud` commands. It is expected that you
have rights to update the Cloud Functions.