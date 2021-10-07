import os
import tempfile

import pandas as pd
from astropy import units as u
from flask import jsonify
from google.cloud import firestore
from google.cloud import storage

PROJECT_ID = os.getenv('PROJECT_ID', 'panoptes-exp')
BUCKET_NAME = os.getenv('BUCKET_NAME', 'panoptes-exp.appspot.com')

storage_client = storage.Client()
output_bucket = storage_client.bucket(BUCKET_NAME)
firestore_db = firestore.Client()


# Entry point
def entry_point(request):
    # Get a real time column
    stats_rows = [d.to_dict()
                  for d
                  in firestore_db.collection('stats').stream()]
    stats_df = pd.DataFrame(stats_rows)

    hours = (stats_df.total_minutes_exptime * u.minute).values.to(u.hour).value

    stats_df['total_hours_exptime'] = [round(x, 2)
                                       for x
                                       in hours]
    stats_df.index = pd.to_datetime(
        stats_df.year.astype(str) + stats_df.week.map(lambda x: f'{x:02d}') + ' SUN',
        format='%Y%W %a'
    )

    columns = {
        'unit_id': 'Unit',
        'week': 'Week',
        'year': 'Year',
        'num_images': 'Images',
        'num_observations': 'Observations',
        'total_minutes_exptime': 'Total Minutes',
        'total_hours_exptime': 'Total Hours'
    }

    # Reorder
    stats_df = stats_df.reindex(columns=list(columns.keys()))

    stats_df.sort_index(inplace=True)
    stats_df.drop(columns=['week', 'year'], inplace=True)

    def reindex_by_date(group):
        dates = pd.date_range(group.index.min(), group.index.max(), freq='W')
        unit_id = group.iloc[0].unit_id
        group = group.reindex(dates).fillna(0)
        group.unit_id = unit_id

        return group

    stats_df = stats_df.groupby(['unit_id']).apply(reindex_by_date).droplevel(0)

    stats_df['year'] = stats_df.index.year
    stats_df['week'] = stats_df.index.week

    stats_df = stats_df.rename(columns=columns)
    stats_df = stats_df.reset_index(drop=True).set_index(['Week'])

    stats_df = stats_df.sort_index()

    # Write out temporary csv.
    with tempfile.TemporaryDirectory() as tmp_dir:
        csv_path = os.path.join(tmp_dir, 'stats.csv')
        stats_df.reset_index().to_csv(csv_path, index=False)

        blob = output_bucket.blob('stats.csv')
        blob.upload_from_filename(csv_path)
        blob.make_public()

    return jsonify(success=True, public_url=blob.public_url)
