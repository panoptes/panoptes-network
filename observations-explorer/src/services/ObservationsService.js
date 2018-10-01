import observations from '../assets/observations.json'

export class ObservationsService {
  constructor () {
    this.name = 'Observations Service'
    this.data = observations.data
    this.total = observations.count
  }
};
