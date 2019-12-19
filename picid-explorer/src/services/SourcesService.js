const request = require('request');
const axios = require('axios').default;

const db = firebase.firestore();
const functions = firebase.functions();

const base_url = 'https://us-central1-panoptes-exp.cloudfunctions.net/get-piaa-details';

export class SourcesService {
  constructor () {
    this.name = 'Sources Service'
  }

  getRecent () {
    return db.collection('picid').limit(100).get();
  }

  getPIAA (piaa_doc_id) {
    return db.doc('piaa/' + piaa_doc_id).get();
  }

  getSource (picid) {
    return db.doc('picid/' + picid).get();
  }

  getSourceObservations (picid) {
    return db.collection('picid/' + picid + '/observations').orderBy('observation_start_time').get();
  }

  getLightcurveData(picid, picid_doc_id){
    return axios.post(base_url, {
        picid: picid,
        document_id: picid_doc_id,
        document: false,
        lightcurve: true
    })
  }
};
