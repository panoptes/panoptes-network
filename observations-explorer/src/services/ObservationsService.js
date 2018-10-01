const axios = require('axios')

export class ObservationsService {
  constructor () {
    this.name = 'Observations Service'
    this.endpoint = 'http://us-central1-panoptes-survey.cloudfunctions.net/get-observations-data'
  }

  getObservations () {
    return axios
      .get(this.endpoint)
  }
};
