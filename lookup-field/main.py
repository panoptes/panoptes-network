from astropy.coordinates import SkyCoord
from panoptes.utils.serializers import to_json


def entry_point(request):
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
    elif request.method == 'GET':
        params = request.args
    elif request.method == 'POST':
        params = request.get_json()

    search_string = params.get('search_string')

    try:
        coord = SkyCoord.from_name(search_string)
        data = dict(
            ra=coord.ra.value,
            dec=coord.dec.value,
            search_string=search_string
        )
        success = True
    except Exception as e:
        print(f'Error in lookup-field: {e!r}')
        data = dict()
        success = False

    # CORS
    headers = {
        'Content-Type': "application/json",
        'Access-Control-Allow-Origin': "*",
    }

    response_body = to_json({'success': success, **data})

    return (response_body, headers)
