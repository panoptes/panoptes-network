Get Observation List
====================

This folder defines a [Google Cloud Function](https://cloud.google.com/functions/).

This function will compile a list of all available observations, along with their
plate-solved RA/Dec coordinates (for the center of the image).

This list can easily be used to search for multiple matching observations based
on coordinates, time, and/or unit_id.

This Cloud Function is called periodically by the Cloud Scheduler.

Endpoint: `/get-observation-list`

Output: https://storage.googleapis.com/panoptes-exp.appspot.com/observations.csv

Example usage:

```python
import pandas as pd
url = 'https://storage.googleapis.com/panoptes-exp.appspot.com/observations.csv'

observations_df = pd.read_csv(url)
```

### Deploy

See [Deployment](../README.md#deploy) in main README for preferred deployment method.
