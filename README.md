# panoptes-network
Software related to the wider PANOPTES network that ties the individual units together.

## PONG - PANOPTES Observatory Network via Google

Software to be used within the Google Cloud Environment (GCE) to network the individual
PANOPTES observatories together.

This also includes some helper utilities for working with various Google products.

## Upload Listener

This Dockerfile runs a script that listens for change notifications on the Storage
bucket associated with observation image uploads.

This effectively serves as the first step in a processing pipeline and acts as a
preprocessor.

See [README](upload-listener/README.md) for details.