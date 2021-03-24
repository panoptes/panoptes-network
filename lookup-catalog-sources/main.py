import base64
import os
import sys
from contextlib import suppress
from io import BytesIO
from typing import Dict, Any, Union

import numpy as np
import requests
from astropy.wcs import WCS
from flask import Flask, request
from google.cloud import firestore
from google.cloud import storage
from panoptes.pipeline.utils import sources
from panoptes.pipeline.utils.gcp.bigquery import get_bq_clients
from panoptes.pipeline.utils.metadata import ObservationPathInfo
from panoptes.pipeline.utils.status import ImageStatus

CURRENT_STATE: ImageStatus = ImageStatus.MATCHING

app = Flask(__name__)

INCOMING_BUCKET: str = os.getenv('INCOMING_BUCKET', 'panoptes-images-solved')
OUTGOING_BUCKET: str = os.getenv('OUTGOING_BUCKET', 'panoptes-images-sources')
ERROR_BUCKET: str = os.getenv('ERROR_BUCKET', 'panoptes-images-error')
SEARCH_PARAMS: Union[str, Dict[Any, int]] = os.getenv('SEARCH_PARAMS',
                                                      dict(vmag_min=6, vmag_max=13, numcont=5))

UNIT_FS_KEY: str = os.getenv('UNIT_FS_KEY', 'units')
OBSERVATION_FS_KEY: str = os.getenv('OBSERVATION_FS_KEY', 'observations')
IMAGE_FS_KEY: str = os.getenv('IMAGE_FS_KEY', 'images')

FITS_HEADER_URL: str = 'https://us-central1-panoptes-exp.cloudfunctions.net/get-fits-header'

# Storage
try:
    firestore_db = firestore.Client()

    storage_client = storage.Client()
    incoming_bucket = storage_client.get_bucket(INCOMING_BUCKET)
    outgoing_bucket = storage_client.get_bucket(OUTGOING_BUCKET)
    error_bucket = storage_client.get_bucket(ERROR_BUCKET)
except RuntimeError:
    print(f"Can't load Google credentials, exiting")
    sys.exit(1)


@app.route("/", methods=["POST"])
def index():
    envelope = request.get_json()
    if not envelope:
        msg = "no Pub/Sub message received"
        print(f"error: {msg!r}")
        return "Invalid pubsub", 400

    if not isinstance(envelope, dict) or "message" not in envelope:
        msg = "invalid Pub/Sub message format"
        print(f"error: {msg!r}")
        return "Invalid pubsub", 400

    pubsub_message = envelope["message"]

    try:
        with suppress(KeyError):
            message_data = base64.b64decode(pubsub_message["data"]).decode("utf-8").strip()
            print(f'Received json {message_data=}')

        # The objectID is stored in the attributes, which is easy to set.
        attributes = pubsub_message["attributes"]
        print(f'Received {attributes=}')

        bucket_path = attributes['objectId']
        print(f'Received bucket_path={bucket_path} for catalog sources lookup')

        url = lookup_sources(bucket_path)
    except Exception as e:
        print(f'Exception in lookup-catalog-sources: {e!r}')
        return '', 204
    else:
        # Success
        # TODO something better here?
        return f'{url}', 204


def lookup_sources(bucket_path):
    # Get information from the path.
    path_info = ObservationPathInfo(path=bucket_path)
    unit_id = path_info.unit_id
    camera_id = path_info.camera_id
    image_time = path_info.image_time

    sequence_id = path_info.sequence_id
    image_id = path_info.image_id

    unit_doc_ref = firestore_db.document((f'{UNIT_FS_KEY}/{unit_id}',))
    seq_doc_ref = unit_doc_ref.collection(OBSERVATION_FS_KEY).document(sequence_id)
    image_doc_ref = seq_doc_ref.collection(IMAGE_FS_KEY).document(image_id)

    with suppress(KeyError, TypeError):
        image_status = image_doc_ref.get(['status']).to_dict()['status']
        if ImageStatus[image_status] >= CURRENT_STATE:
            print(f'Skipping image with status of {ImageStatus[image_status].name}')
            return True

    print(f'Setting image {image_doc_ref.id} to {CURRENT_STATE.name}')
    image_doc_ref.set(dict(status=CURRENT_STATE.name), merge=True)

    ra_column = 'catalog_ra'
    dec_column = 'catalog_dec'
    origin = 1

    # Save the file - ugly replace
    sources_bucket_path = bucket_path.replace('.fits.fz', '.csv').replace('.fits', '.csv')

    outgoing_blob = outgoing_bucket.blob(sources_bucket_path)
    if outgoing_blob.exists():
        raise FileExistsError(f'File already exists at {outgoing_blob.public_url}')

    try:
        header_dict = lookup_fits_header(bucket_path)
    except KeyError:
        return Exception(f'No FITS header for {bucket_path} in {INCOMING_BUCKET}')
    wcs0 = WCS(header_dict)

    print(f'Looking up sources for {sequence_id} {wcs0}')
    bq_client, bqstorage_client = get_bq_clients()
    catalog_sources = sources.get_stars_from_wcs(wcs0,
                                                 bq_client=bq_client,
                                                 bqstorage_client=bqstorage_client,
                                                 **SEARCH_PARAMS
                                                 )
    print(f'Found {len(catalog_sources)} sources in {sequence_id}')

    # Get the XY positions via the WCS
    catalog_coords = catalog_sources[[ra_column, dec_column]]
    catalog_xy = wcs0.all_world2pix(catalog_coords, origin, ra_dec_order=True)
    catalog_sources['catalog_wcs_x'] = catalog_xy.T[0]
    catalog_sources['catalog_wcs_y'] = catalog_xy.T[1]
    catalog_sources['catalog_wcs_x_int'] = catalog_sources.catalog_wcs_x.astype(int)
    catalog_sources['catalog_wcs_y_int'] = catalog_sources.catalog_wcs_y.astype(int)

    # Get additional metadata.
    catalog_sources['unit_id'] = unit_id
    catalog_sources['sequence_id'] = sequence_id
    catalog_sources['camera_id'] = camera_id
    catalog_sources['time'] = image_time

    # We index some of the database on the vmag bin, so precompute it.
    catalog_sources.catalog_vmag_bin = catalog_sources.catalog_vmag.apply(np.floor).astype('int')

    catalog_sources.drop(columns=['unit_id', 'sequence_id', 'camera_id'])

    # Write directly to in-memory file, avoiding the disk.
    bio = BytesIO()
    catalog_sources.convert_dtypes().dropna().to_csv(bio, index=False)
    bio.seek(0)

    # Upload
    outgoing_blob.upload_from_file(bio)
    print(f'Observation metadata saved to {outgoing_blob.public_url}')

    print(f'Recording firestore metadata for {bucket_path}')
    image_doc_updates = dict(
        status=ImageStatus(CURRENT_STATE + 1).name,
        has_sources=True,
        sources_url=outgoing_blob.public_url,
    )

    # Record the metadata in firestore.
    image_doc_ref.set(
        image_doc_updates,
        merge=True
    )

    return outgoing_blob.public_url


def lookup_fits_header(bucket_path):
    """Read the FITS header from storage. """
    header = None
    request_params = dict(bucket_path=bucket_path, bucket_name=INCOMING_BUCKET)
    res = requests.post(FITS_HEADER_URL, json=request_params)
    if res.ok:
        header = res.json()['header']

    return header
