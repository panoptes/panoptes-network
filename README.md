# PANOPTES Network

Software related to the wider PANOPTES network that ties the individual units together.
This is a repository to host the various Google Cloud Environment techonologies,
such as the Cloud Funcitions (CF) and any AppEngine definitions.

Each subfolder defines a different serivce and the services should be used from
their respective directories. Each directory has a specific README.

## POE - PANOPTES Observations Explorer
<a id="observations-explorer"></a>

A simple table display of the Observations. This reads JSON files that are provided
via the [Observations Data CF](#observations-data)

See [README](observations-explorer/README.md).

## Observations Data
<a id="observatons-data"></a>

A JSON service for the observations data.

See [README](observations-data/README.md).
