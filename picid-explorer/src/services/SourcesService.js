const request = require('request');
const db = firebase.firestore();
const functions = firebase.functions();

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

  getLightcurveData (url) {
    return request.get(url);
  }
};



