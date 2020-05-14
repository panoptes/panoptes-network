Get Recent Observations
=======================

This folder defines a [Google Cloud Function](https://cloud.google.com/functions/).

This function will compile the recent observations into a csv file. This function is
called periodically by the cloud scheduler and should not need to be called manually.

By default the csv will include the last 100 observations.

Endpoint: `/get-recent-observations`

Output: https://storage.googleapis.com/panoptes-exp.appspot.com/recent.csv

Example usage:

```python
import pandas as pd
url = 'https://storage.googleapis.com/panoptes-exp.appspot.com/recent.csv'

recent_obs_df = pd.read_csv(url)
```

### Deploy

See [Deployment](../README.md#deploy) in main README for preferred deployment method.
