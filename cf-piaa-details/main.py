from google.cloud import firestore
from astropy.stats import sigma_clip
import pandas as pd
from panoptes.utils.serializers import to_json

try:
    db = firestore.Client()
except Exception as e:
    print(f'Error getting firestore client: {e!r}')


def get_piaa_details(request):
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
    # Set CORS headers for the preflight request
    if request.method == 'OPTIONS':
        # Allows GET requests from any origin with the Content-Type
        # header and caches preflight response for an 3600s
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '3600'
        }

        return ('', 204, headers)

    request_json = request.get_json()
    if request_json is None:
        request_json = request.args

    picid = request_json['picid']
    document_id = request_json['document_id']

    # Data types to get
    get_document = request_json.get('document', True)
    should_get_metadata = request_json.get('metadata', False)
    should_get_metadata = False  # For now
    should_get_lightcurve = request_json.get('lightcurve', False)
    should_get_psc = request_json.get('psc', False)
    should_get_counts = request_json.get('counts', False)

    # Fetch the document
    piaa_doc = db.document(f'picid/{picid}/observations/{document_id}').get().to_dict()

    # Get the urls from the document
    comparison_url = piaa_doc['files']['comparison-psc']
    target_url = piaa_doc['files']['target-psc']
    lightcurve_url = piaa_doc['files']['lightcurve-data']
    metadata_url = piaa_doc['files']['reference-metadata']

    response = dict()

    try:
        if get_document:
            response = piaa_doc

        if should_get_metadata:
            response['metadata'] = get_metadata(metadata_url).to_dict(orient='record')

        if should_get_lightcurve:
            response['lightcurve'] = get_lightcurve(lightcurve_url).to_dict(orient='list')

        if should_get_psc:
            response['psc'] = get_psc(target_url, comparison_url).to_dict(orient='list')

        if should_get_counts:
            metadata_df = get_metadata(metadata_url)
            psc_df = get_psc(target_url, comparison_url)
            response['counts'] = get_counts(picid, metadata_df, psc_df).to_dict(orient='list')
    except Exception as e:
        response_body = to_json({'Error': e})
    else:
        response_body = to_json(response)

    # CORS
    headers = {
        'Content-Type': "application/json",
        'Access-Control-Allow-Origin': "*",
    }

    return (response_body, headers)


def get_psc(target_url, comparison_url):
    # Get the data
    target_psc0 = pd.read_csv(target_url, parse_dates=True)
    comp_psc0 = pd.read_csv(comparison_url, parse_dates=True)

    # Rename the columns
    target_psc0.columns = ['image_time'] + [f'pixel_{i:02d}' for i in range(len(target_psc0.columns) - 1)]
    comp_psc0.columns = ['image_time'] + [f'pixel_{i:02d}' for i in range(len(comp_psc0.columns) - 1)]

    # Put into tidy format
    target_psc1 = target_psc0.melt(id_vars=['image_time'], var_name='pixel')
    comp_psc1 = comp_psc0.melt(id_vars=['image_time'], var_name='pixel')

    # Mark the source
    target_psc1['source'] = 'target'
    comp_psc1['source'] = 'reference'

    # Create single dataframe
    psc = pd.concat([target_psc1, comp_psc1])
    psc.image_time = pd.to_datetime(psc.image_time)

    return psc


def get_metadata(metadata_url):
    # Get data
    metadata_df = pd.read_csv(metadata_url)

    # Remove columns
    metadata_df.drop(columns=['Unnamed: 0', 'seq_time', 'unit_id', 'camera_id'], inplace=True)

    return metadata_df


def get_lightcurve(lightcurve_url):
    # Get data
    lc_df0 = pd.read_csv(lightcurve_url, parse_dates=True)
    lc_df0.image_time = pd.to_datetime(lc_df0.image_time)
    lc_df0.sort_values(by='image_time')

    # Mark those values that would be sigma clipped
    for color in list('rgb'):
        lc_df0[f'{color}_outlier'] = sigma_clip(lc_df0[color]).mask

    return lc_df0


def get_counts(picid, metadata_df, psc_df):
    flux = psc_df.groupby(['source', 'image_time']).value.sum().reset_index()

    raw_target_flux = metadata_df.query('picid == @picid').filter(['picid', 'image_time', 'flux_best', 'fluxerr_best'])
    raw_target_flux.image_time = pd.to_datetime(raw_target_flux.image_time)
    raw_target_flux.drop(columns=['picid', 'fluxerr_best'], inplace=True)

    fluxes = pd.concat([
        flux,
        raw_target_flux.melt(id_vars=['image_time'], var_name='source')
    ], sort=False)

    # Return in long format
    return fluxes.pivot(index='image_time', columns='source', values='value').reset_index()
