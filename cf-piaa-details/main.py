import sys
import traceback
import numpy as np
from google.cloud import firestore
from astropy.stats import sigma_clip
from astropy import units as u
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

    should_get_recent_list = request_json.get('recent_picid', False)
    should_search_picid = request_json.get('search_picid', False)

    picid = request_json.get('picid', None)
    picid_doc_id = request_json.get('picid_doc_id', None)

    # Data types to get
    should_get_source_doc = request_json.get('source_info', False)
    should_get_piaa_runs = request_json.get('piaa_runs', False)

    should_get_piaa_doc = request_json.get('piaa_document', False)

    should_get_metadata = request_json.get('metadata', False)
    should_get_metadata = False  # For now

    should_get_lightcurve = request_json.get('lightcurve', False)
    should_get_psc = request_json.get('psc', False)
    should_get_counts = request_json.get('counts', False)
    should_get_pixel_drift = request_json.get('pixel_drift', False)
    should_get_ref_locations = request_json.get('ref_locations', False)

    if picid:
        # Get the document for the star.
        source_ref = db.document(f'picid/{picid}')

        if picid_doc_id:
            piaa_doc = source_ref.collection(f'observations').document(f'{picid_doc_id}').get().to_dict()
            piaa_run_doc_ref = db.document('piaa/{}'.format(piaa_doc['piaa_document_id']))
            piaa_doc['piaa_doc'] = piaa_run_doc_ref.get().to_dict()
            piaa_doc['source'] = source_ref.get().to_dict()
            piaa_doc['rms'] = piaa_run_doc_ref.collection('rms').document(f'{picid}').get().to_dict()

            # Get the urls from the document
            comparison_url = piaa_doc['files']['comparison-psc']
            target_url = piaa_doc['files']['target-psc']
            lightcurve_url = piaa_doc['files']['lightcurve-data']
            metadata_url = piaa_doc['files']['reference-metadata']

    response = dict()

    try:
        if should_get_recent_list:
            recent_list = pd.DataFrame([{'id': doc.id,
                                         **doc.to_dict()}
                                        for doc
                                        in db.collection('picid').order_by('last_process_time',
                                                                           direction='DESCENDING').limit(50).stream()])

            response['picid'] = recent_list.fillna('Unknown').to_dict(orient='records')

        if should_search_picid:
            try:
                search_model = request_json['search_model']
            except KeyError:
                response_body = to_json({'Error': f'Missing search parameters'})

            # First convert the units if needed
            ra_radius = search_model['raRadius'] * u.Unit(search_model['radiusUnits'].lower())
            dec_radius = search_model['decRadius'] * u.Unit(search_model['radiusUnits'].lower())

            # Convert units to degrees
            ra_radius = ra_radius.to('degree').value
            dec_radius = dec_radius.to('degree').value

            ra_search = search_model['ra']
            dec_search = search_model['dec']
            vmag_lower, vmag_upper = search_model['vmagRange']

            # Filter the RA on the server and then filter others below
            search_results = db.collection('picid') \
                .where('dec', '>=', dec_search - dec_radius) \
                .where('dec', '<=', dec_search + dec_radius) \
                .stream()
            recent_list = pd.DataFrame([{'id': doc.id,
                                         **doc.to_dict()}
                                        for doc
                                        in search_results])

            # Filter Dec and Vmag
            filter_string = f'ra >= {ra_search - ra_radius}'
            filter_string += f' and ra <= {ra_search + ra_radius}'
            filter_string += f' and vmag >= {vmag_lower}'
            filter_string += f' and vmag <= {vmag_upper}'
            recent_list = recent_list.query(filter_string).copy()

            # Limit number by radial distance
            recent_list['distance'] = np.sqrt(
                (recent_list['ra'] - ra_search)**2 +
                (recent_list['dec'] - dec_search)**2
            )
            recent_list = recent_list.sort_values(by='distance').iloc[:200]

            response['picid'] = recent_list.fillna('Unknown').to_dict(orient='records')

        if should_get_source_doc:
            source_doc = source_ref.get().to_dict()
            if source_doc['lumclass'] not in ['GIANT', 'DWARF']:
                source_doc['lumclass'] = 'Unknown'
            response['picid_document'] = source_doc

        if should_get_piaa_runs:
            response['piaa_runs'] = [
                {'id': doc.id, **doc.to_dict()}
                for doc
                in source_ref.collection(f'observations').order_by('observation_start_time').stream()
            ]

        if should_get_piaa_doc:
            response['piaa_document'] = piaa_doc

        if should_get_metadata:
            response['metadata'] = get_metadata(metadata_url).to_dict(orient='record')

        if should_get_lightcurve:
            response['lightcurve'] = get_lightcurve(lightcurve_url).to_dict(orient='list')

        if should_get_psc:
            assert picid_doc_id is not None, "PIAA Document ID required"
            response['psc'] = get_psc(target_url, comparison_url)

        if should_get_counts:
            metadata_df = get_metadata(metadata_url)
            psc_df = get_psc(target_url, comparison_url, tidy=True)
            response['counts'] = get_counts(picid, metadata_df, psc_df).to_dict(orient='list')

        if should_get_pixel_drift:
            metadata_df = get_metadata(metadata_url)
            response['pixel_drift'] = get_pixel_drift(picid, metadata_df).to_dict(orient='list')

        if should_get_ref_locations:
            metadata_df = get_metadata(metadata_url)
            response['ref_locations'] = get_ref_locations(metadata_df).to_dict(orient='list')

    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        response_body = to_json({'Error': f'{e!r}'})
    else:
        response_body = to_json(response)

    # CORS
    headers = {
        'Content-Type': "application/json",
        'Access-Control-Allow-Origin': "*",
    }

    return (response_body, headers)


def get_psc(target_url, comparison_url, tidy=False):
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

    if tidy is False:
        stamp_size = int(np.sqrt(len(psc.pixel.unique())))

        # Get the pixel ordered (because we don't have proper string numbering)
        psc.pixel = psc.pixel.apply(lambda x: x.split('_')[-1]).astype(np.int)

        psc = {
            'target': psc.query('source == "target"').sort_values(by=['image_time', 'pixel']).value.values.reshape(-1, stamp_size, stamp_size),
            'comparison': psc.query('source == "reference"').sort_values(by=['image_time', 'pixel']).value.values.reshape(-1, stamp_size, stamp_size)
        }

    return psc


def get_metadata(metadata_url):
    # Get data
    metadata_df = pd.read_csv(metadata_url)

    # Remove columns
    metadata_df.drop(columns=['Unnamed: 0', 'seq_time', 'unit_id', 'camera_id'], inplace=True, errors='ignore')

    return metadata_df


def get_lightcurve(lightcurve_url, sample_time=30):
    # Get data
    lc_df0 = pd.read_csv(lightcurve_url, parse_dates=True)
    lc_df0.image_time = pd.to_datetime(lc_df0.image_time)
    lc_df0.sort_values(by='image_time', inplace=True)

    # Mark those values that would be sigma clipped
    for color in list('rgb'):
        lc_df0[f'{color}_outlier'] = sigma_clip(lc_df0[color]).mask

    # lc_df1 = lc_df0.set_index('image_time').groupby('color').resample(f'{sample_time}T').median()

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

    # Return in tidy format
    return fluxes.pivot(index='image_time', columns='source', values='value').reset_index()


def get_pixel_drift(picid, metadata_df):
    pixel_df = metadata_df.query('picid == @picid').filter(['image_time', 'x', 'y'])
    pixel_df.image_time = pd.to_datetime(pixel_df.image_time)
    pixel_df.sort_values(by='image_time', inplace=True)

    pixel_df['x_offset'] = pixel_df.x - pixel_df.iloc[0].x
    pixel_df['y_offset'] = pixel_df.y - pixel_df.iloc[0].y

    return pixel_df


def get_ref_locations(metadata_df):
    location_df = metadata_df.groupby(['picid']).median().filter([
        'x', 'y', 'score', 'score_rank', 'coeffs'
    ]).reset_index()

    # Fix score rank for multiindex
    location_df['score_rank'] = location_df.score_rank.rank()

    location_df.sort_values(by='score', inplace=True)

    # Target doesn't have a coeff, but we don't use anyway.
    location_df.fillna(value=0, inplace=True)

    return location_df
