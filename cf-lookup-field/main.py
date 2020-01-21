from flask import jsonify
from astropy.coordinates import SkyCoord


def lookup_field(request):
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
    if request.args and 'search_string' in request.args:
        search_string = request.args.get('search_string')
    elif request_json and 'search_string' in request_json:
        search_string = request_json['search_string']
    else:
        return f'No search string specified'

    try:
        coord = SkyCoord.from_name(search_string)
        data = dict(ra=coord.ra.value, dec=coord.dec.value)
    except Exception:
        data = dict()

    return jsonify(data=data)
