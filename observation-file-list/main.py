from flask import Response
import requests

obs_data_endpoint = 'https://us-central1-panoptes-survey.cloudfunctions.net/get-observations-data'


def get_file_list(request):
    """ENTRYPOINT - get the observataion file list """
    request_json = request.get_json()

    sequence_id = None
    if request_json and 'sequence_id' in request_json:
        sequence_id = request_json['sequence_id']
    elif request.args and 'sequence_id' in request.args:
        sequence_id = request.args['sequence_id']

    # We will place any items to return in this list
    items = list()

    if sequence_id:
        print("Looking up file list for sequence_id={}".format(sequence_id))

        res = requests.get(obs_data_endpoint, params={'sequence_id': sequence_id})
        res_json = res.json()

        print(f'Response: {res_json!r}')

        try:
            items = sorted(res_json['items']['sequence_files']['fz'])
        except Exception as e:
            print(f'Problem with json response: {e}')
            items = list()

    print("Found {} rows".format(len(items)))

    return Response('\n'.join(items), mimetype="text/plain",
                    headers={"Content-Disposition":
                             f"attachment;filename={sequence_id}.txt"})
