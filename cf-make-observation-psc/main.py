import os
from contextlib import suppress

from flask import jsonify
from google.cloud import storage
import pandas as pd
import requests

PROJECT_ID = os.getenv('PROJECT_ID', 'panoptes-survey')
BUCKET_NAME = os.getenv('BUCKET_NAME', 'panoptes-detected-sources')
UPLOAD_BUCKET = os.getenv('UPLOAD_BUCKET', 'panoptes-observation-psc')
client = storage.Client(project=PROJECT_ID)
bucket = client.get_bucket(BUCKET_NAME)

update_state_url = os.getenv(
    'HEADER_ENDPOINT',
    'https://us-central1-panoptes-survey.cloudfunctions.net/update-state'
)

TMP_DIR = '/tmp'


def make_observation_psc(request):
    """Responds to any HTTP request.

    Notes:
        rawpy params: https://letmaik.github.io/rawpy/api/rawpy.Params.html
        rawpy enums: https://letmaik.github.io/rawpy/api/enums.html

    Args:
        request (flask.Request): HTTP request object.
    Returns:
        The response text or any set of values that can be turned into a
        Response object using
        `make_response <http://flask.pocoo.org/docs/1.0/api/#flask.Flask.make_response>`.
    """
    request_json = request.get_json()
    if request.args and 'sequence_id' in request.args:
        sequence_id = request.args.get('sequence_id')
    elif request_json and 'sequence_id' in request_json:
        sequence_id = request_json['sequence_id']
    else:
        return f'No observation (sequence_id) requested'

    min_num_frames = request_json.get('min_num_frames', 10)
    frame_threshold = request_json.get('frame_threshold', .98)

    print(f'Sequence ID: {sequence_id}')

    bucket_path = sequence_id.replace('_', '/')
    # Add trailing slash for lookups
    if bucket_path.endswith('/') is False:
        bucket_path = f'{bucket_path}/'
    print(f'Getting CSV files in bucket: {bucket_path}')
    csv_blobs = bucket.list_blobs(prefix=bucket_path, delimiter='/')

    # Add the CSV files one at a time.
    df_list = dict()
    try:
        for blob in csv_blobs:
            print(f'Getting blob name {blob.name}')
            tmp_fn = os.path.join(TMP_DIR, blob.name.replace('/', '_'))
            print(f'Downloading to {tmp_fn}')
            blob.download_to_filename(tmp_fn)

            print(f'Making DataFrame for {tmp_fn}')
            df0 = pd.read_csv(tmp_fn)

            # Cleanup columns
            df0.drop(columns=['unit_id', 'camera_id', 'sequence_time'], inplace=True)
            df_list[tmp_fn] = df0

        if len(df_list) <= min_num_frames:
            state = 'error_seq_too_short'
            msg = f'Not enough CSV files found for {sequence_id}: {len(df_list)} files found'
            requests.post(update_state_url, json={'sequence_id': sequence_id, 'state': state})
            return jsonify(success=False, msg=msg)

        print(f'Making PSC DataFrame for {sequence_id}')
        psc_df = pd.concat(list(df_list.values()), sort=False)

        # Only keep the keys (filenames)
        df_list = list(df_list.keys())

        # Make a datetime index
        psc_df.index = pd.to_datetime(psc_df.image_time)
        psc_df.drop(columns=['image_time'])

        # Make the PICID (as str) an index
        psc_df.picid = psc_df.picid.astype(str)
        psc_df.set_index(['picid'], inplace=True, append=True)
        psc_df.sort_index(inplace=True)

        # Report
        num_sources = len(psc_df.index.levels[1].unique())
        num_frames = len(set(psc_df.index.levels[0].unique()))
        print(f"Sequence: {sequence_id} Frames: {num_frames} Sources: {num_sources}")

        # Get minimum frame threshold
        frame_count = psc_df.groupby('picid').count().pixel_00
        min_frame_count = int(frame_count.max() * frame_threshold)
        print(f'Sequence: {sequence_id} Frames: {frame_count.max()} Min cutout: {min_frame_count}')

        # Filter out the sources where the number of frames is less than min_frame_count
        def has_frame_count(grp):
            return grp.count()['pixel_00'] >= min_frame_count

        # Do the actual fileter an reset the index
        print(f'Sequence: {sequence_id} filtering sources')
        psc_df = psc_df.reset_index() \
            .groupby('picid') \
            .filter(has_frame_count) \
            .set_index(['image_time', 'picid'])

        # Report again
        num_sources = len(psc_df.index.levels[1].unique())
        num_frames = len(set(psc_df.index.levels[0].unique()))
        print(f"Frames: {num_frames} Sources: {num_sources}")

        # Write to file
        out_fn = sequence_id.replace('/', '_')
        if out_fn.endswith('_'):
            out_fn = out_fn[:-1]
        out_fn = os.path.join(TMP_DIR, f'{out_fn}.csv')
        print(f'Writing DataFrame to {out_fn}')
        psc_df.to_csv(out_fn)

        upload_bucket_path = f'{sequence_id}.csv'.replace('_', '/')

        print(f'Uploading {out_fn} to {upload_bucket_path}')
        upload_blob(out_fn, upload_bucket_path)

        print(f'Removing {out_fn}')
        os.remove(out_fn)

        state = 'psc_created'
        print(f'Updating state for {sequence_id} to {state}')
        requests.post(update_state_url, json={'sequence_id': sequence_id, 'state': state})

    finally:
        print(f'Removing all downloaded files for {sequence_id}')
        for tmp_fn in df_list:
            with suppress(FileNotFoundError):
                os.remove(tmp_fn)

        success_msg = f"PSC file created for {sequence_id}"

    return jsonify(success=True, msg=success_msg)


def upload_blob(source_file_name, destination_blob_name, bucket=None):
    """Uploads a file to the bucket."""
    if bucket is None:
        bucket = client.get_bucket(UPLOAD_BUCKET)

    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)

    print('File {} uploaded to {}.'.format(source_file_name, destination_blob_name))
