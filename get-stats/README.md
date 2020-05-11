Get Stats
=========

This folder defines a [Google Cloud Function](https://cloud.google.com/functions/).

This function will compile the `stats` collection into a csv file. This function is
called periodically by the cloud scheduler and should not need to be called manually.

Endpoint: `/get-stats`

Output: https://storage.googleapis.com/panoptes-exp.appspot.com/stats.csv

Example usage (typically indexed by `Week` and `Unit`):

```python
import pandas as pd
url = 'https://storage.googleapis.com/panoptes-exp.appspot.com/stats.csv'
stats_df pd.read_csv(url).sort_values(by=['Week', 'Unit']).set_index(['Week'])

stats_df.head()
```


|   Week | Unit   |   Images |   Observations |   Total Minutes |   Total Hours |   Year |
|-------:|:-------|---------:|---------------:|----------------:|--------------:|-------:|
|      1 | PAN001 |        0 |              0 |               0 |          0    |   2018 |
|      1 | PAN001 |        0 |              0 |               0 |          0    |   2019 |
|      1 | PAN001 |      226 |              4 |             452 |          7.53 |   2017 |
|      1 | PAN001 |     2290 |             37 |            2290 |         38.17 |   2020 |
|      1 | PAN008 |        0 |              0 |               0 |          0    |   2019 |




### Deploy

See [Deployment](../README.md#deploy) in main README for preferred deployment method.
