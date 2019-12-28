const axios = require('axios').default;

const base_url = 'https://us-central1-panoptes-exp.cloudfunctions.net/get-piaa-details';

export class SourcesService {
  constructor () {
    this.name = 'Sources Service'
  }

  getRecent () {
    return axios.post(base_url, {
      recent_picid: true
    })
  }

  getSource (picid) {
    return axios.post(base_url, {
        picid: picid,
        source_info: true
    })
  }

  getSourceObservations (picid) {
    return axios.post(base_url, {
        picid: picid,
        piaa_runs: true
    })
  }

  getPIAA (picid, picid_doc_id) {
    return axios.post(base_url, {
        picid: picid,
        picid_doc_id: picid_doc_id,
        piaa_document: true
    })
  }

  getLightcurveData(picid, picid_doc_id){
    return axios.post(base_url, {
        picid: picid,
        picid_doc_id: picid_doc_id,
        lightcurve: true
    })
  }

  getPSC(picid, picid_doc_id){
    return axios.post(base_url, {
        picid: picid,
        picid_doc_id: picid_doc_id,
        psc: true
    })
  }

  getRawCounts(picid, picid_doc_id){
    return axios.post(base_url, {
        picid: picid,
        picid_doc_id: picid_doc_id,
        counts: true
    })
  }

  getPixelDrift(picid, picid_doc_id){
    return axios.post(base_url, {
        picid: picid,
        picid_doc_id: picid_doc_id,
        pixel_drift: true
    })
  }

  getReferenceLocations(picid, picid_doc_id){
    return axios.post(base_url, {
        picid: picid,
        picid_doc_id: picid_doc_id,
        ref_locations: true
    })
  }
};
