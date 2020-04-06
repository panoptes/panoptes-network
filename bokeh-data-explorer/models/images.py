import requests
import pandas as pd

from models.base import BaseModel


class Model(BaseModel):

    def __init__(self):
        super().__init__()

    def fetch_data(self, sequence_id):

        url = 'https://us-central1-panoptes-exp.cloudfunctions.net/get-images'
        # print(f'Getting documents for {sequence_id}')

        res = requests.post(url, json=dict(sequence_id=sequence_id, tidy=False))

        if res.ok:
            images = pd.DataFrame(res.json())
            images['image_path'] = images.bucket_path.str.replace('processed', 'raw').str.replace('.fits.fz', '.jpg')
            images.time = pd.to_datetime(images.time, unit='s')
            images.sort_values(by='time', inplace=True)

        return images
