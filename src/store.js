import Vue from 'vue'
import Vuex from 'vuex'

import moment from 'moment';

// Firebase App (the core Firebase SDK) is always required and
// must be listed before other Firebase SDKs
// const firebase = require("firebase");
// Required for side-effects
// require("firebase/firestore");

// const firebaseConfig = {
//   apiKey: "AIzaSyCObINzchGuOAauuzEX3nj6iNJU-YSM4Cg",
//   authDomain: "panoptes-exp.firebaseapp.com",
//   projectId: "panoptes-exp",
//   databaseURL: "https://panoptes-exp.firebaseio.com",
//   storageBucket: "panoptes-exp.appspot.com",
//   messagingSenderId: "21247607123",
//   appId: "1:21247607123:web:0605d362b8c98321e4e1a6"
// };
// firebase.initializeApp(firebaseConfig);
const db = firebase.firestore();

const axios = require('axios').default;
const base_url = 'https://us-central1-panoptes-exp.cloudfunctions.net';

Vue.use(Vuex)

export default new Vuex.Store({
  state: {
      picid: null,
      frameIndex: 0,
      totalFrames: null,
      observations: [],
      sources: [],
      sourceRecord: null,
      sourceRunDetail: null,
      piaaRecord: null,
      locationData: {},
      stampData: {},
      lightcurveData: {},
      rawData: {},
      pixelData: {},
      fromSearch: false,
      isSearching: false,
      units: [],
      searchModel: {
        modalActive: false,
        isSearching: {
          'observations': false,
          'picid': false,
          'general': false,
        },
        vmagRange: [8, 10],
        radiusUnits: ['Degree', 'Arcmin', 'Arcsec'],
        radiusUnit: 'Degree',
        searchRadius: 5,
        searchString: 'M42',
        ra: 83.822,
        dec: -5.931,
        valid: false,
        startDate: null,
        endDate: null,
        selectedUnits: []
    }
  },
  mutations: {
      setSource(state, picid) {
        state.picid = picid;
      },
      resetState(){
        state.observations = [];
        state.sourceRecord = null;
        state.sourceRunDetail = null;
        state.piaaRecord = null;
        state.locationData = {};
        state.stampData = {};
        state.lightcurveData = {};
        state.rawData = {};
        state.plotData = {};
        state.frameIndex = 0;
        state.totalFrames = null;
      },
      setFrame(state, record) {
        state.frameIndex = record;
        if (state.frameIndex == state.totalFrames){
          state.frameIndex = 0;
        }
        if (state.frameIndex == -1){
          state.frameIndex = state.totalFrames - 1;
        }
      },
      setSearchCoords(state, record) {
        if (record !== undefined){
          state.searchModel.ra = record.ra.toFixed(3);
          state.searchModel.dec = record.dec.toFixed(3);
          state.searchModel.radiusUnit = 'Degree';
        }
      },
      setFrameSize(state, record) { state.totalFrames = record },
      setSearchModel(state, model) { state.searchModel = model },

      setObservations(state, records){ state.observations = records },
      setSources(state, rows) { state.sources = rows },

      setSourceRecord(state, record) { state.sourceRecord = record },
      setRunDetail(state, record){ state.sourceRunDetail = record },
      setPiaaRecord(state, record){ state.piaaRecord = record },

      setLocationData(state, record){ state.locationData = record },
      setStampData(state, record){ state.stampData = record },
      setLightcurveData(state, record){ state.lightcurveData = record },
      setPixelData(state, record){ state.pixelData = record },
      setRawCounts(state, record){ state.rawData = record },

      addObservationRun(state, data) { state.observations.push(data) },
      addUnit(state, data) { state.units.push(data) },

      setFromSearch(state, fromSearch) { state.fromSearch = fromSearch },

      setSearching(state, loadingType, is_loading) {
        state.searchModel.isSearching[loadingType] = is_loading;
      },

      toggleSearchForm(state, model) {
        state.searchModel.modalActive = !state.searchModel.modalActive
      }
  },
  actions: {
      setFrame({ commit, state }, newIndex ){ commit('setFrame', newIndex) },
      setSource({ commit, state }, picid) {
        // Set property
        commit('resetState');
        commit('setSource', picid);

        // Get all the observation proessing runs for source.
        state.sources.getSourceObservations(state.picid).then((response) => {
          if (response.status == 200){
            commit('setObservations', response.data.piaa_runs);
          }
        })
        .catch((err) => {
          console.log('Error getting observation runs', err);
        });

        state.sources.getSource(state.picid).then((response) => {
          if (response.status == 200){
            commit('setSourceRecord', response.data.picid_document);
          }
        })
        .catch((err) => {
          console.log('Error getting documents', err);
        });
      },

      selectRow: function({ commit, state, dispatch }, row) {
        commit('setRunDetail', row);

        commit('setPiaaRecord', {});
        state.sources.getPIAA(state.picid, row.id)
        .then((response) => {
          if (response.status == 200){
            commit('setPiaaRecord', response.data.piaa_document);
          }
        })
        .catch((err) => { console.log('Error getting PIAA details', err); });

        dispatch('getLightcurve');
        dispatch('getRawCounts');
        dispatch('getReferenceLocations');
        dispatch('getPixelDrift');
        dispatch('getPSC');
      },

      getLightcurve: function({ commit, state }) {
        commit('setLightcurveData', {})
        state.sources.getLightcurveData(state.picid, state.sourceRunDetail.id).then((response) => {
          if (response.status == 200){
            commit('setLightcurveData', response.data.lightcurve)
          }
        }).catch(function(error){
          console.log(error)
        });
      },

      getPSC: function({ commit, state }) {
        commit('setStampData', {})
        state.sources.getPSC(state.picid, state.sourceRunDetail.id).then((response) => {
          if (response.status == 200){
            commit('setStampData', response.data.psc)
            commit('setFrameSize', response.data.psc.target.length)
          }
        }).catch(function(error){
          console.log(error)
        });
      },

      getRawCounts: function({ commit, state }) {
        commit('setRawCounts', {})
        state.sources.getRawCounts(state.picid, state.sourceRunDetail.id).then((response) => {
          if (response.status == 200){
            commit('setRawCounts', response.data.counts)
          }
        });
      },

      getPixelDrift: function({ commit, state }) {
        commit('setPixelData', {});
        state.sources.getPixelDrift(state.picid, state.sourceRunDetail.id).then((response) => {
          if (response.status == 200){
            commit('setPixelData', response.data.pixel_drift);
          }
        });
      },

      getReferenceLocations: function({ commit, state }) {
        commit('setLocationData', {})
        state.sources.getReferenceLocations(state.picid, state.sourceRunDetail.id).then((response) => {
          if (response.status == 200){
            commit('setLocationData', response.data.ref_locations)
          }
        });
      },

      getRecent: function({ dispatch }) {
        dispatch('getRecentObservations');
        dispatch('getRecentSources');
      },

      getRecentObservations: function({ commit, state }) {
        db.collection('observations').orderBy('time', 'desc').limit(25).get()
          .then((querySnapshot) => {
            let rows = [];
            querySnapshot.forEach((doc) => {
                let data = doc.data();
                data['sequence_id'] = doc.id;
                data['time'] = moment(data['time'].toDate());
                rows.push(data);
            });
            commit('setObservations', rows);
          })
          .catch(err => {
            console.log('Error getting recent observations', err)
          });
      },

      getRecentSources: function({ commit, state }) {
        db.collection('picid').orderBy('last_process_time', 'desc').limit(25).get()
          .then((querySnapshot) => {
            let rows = [];
            querySnapshot.forEach((doc) => {
                let data = doc.data();
                data['picid'] = doc.id;
                data['last_process_time'] = moment(data['last_process_time'].toDate());
                rows.push(data);
            });
            commit('setSources', rows);
          })
          .catch(err => {
            console.log('Error getting recent observations', err)
          });
      },

      getUnits: function({ commit, state }) {
        db.collection("units").get().then((querySnapshot) => {
          querySnapshot.forEach((doc) => {
              let data = doc.data();
              data['unit_id'] = doc.id;
              commit('addUnit', data);
          });
        }).catch((err) => {
          console.log('Error in getUnits:', err);
        });
      },

      lookupField: function({ commit, state }) {
         commit('setSearching', 'general', true);
         axios.post(base_url + '/lookup-field', {
           'search_string': state.searchModel.searchString
         }).then((response) => {
           if (response.status == 200){
             commit('setSearchCoords', response.data);
             commit('setSearching', 'general', false);
           }
         }).catch((err) => {
           console.log("Error looking up field names");
           console.log(err)
         }).finally();
      },

      searchObservations: function({ commit, state } ){
        commit('setObservations', []);
        commit('setSearching', 'observations', true);
        db.collection('observations')
          .where('field_dec', '>=', state.searchModel.dec - state.searchModel.searchRadius)
          .where('field_dec', '<=', state.searchModel.dec + state.searchModel.searchRadius)
          .orderBy('dec')
          .orderBy('time', 'desc')
          .get().then(querySnapshot => {
            querySnapshot.docs.forEach((doc) => {
              let data = doc.data();
              data['sequence_id'] = doc.id;
              if (data.ra >= state.searchModel.ra - state.searchModel.searchRadius){
                return false;
              }
              if (data.ra <= state.searchModel.ra + state.searchModel.searchRadius){
                return false;
              }

              // Todo: filter date here.

              data['time'] = moment(data['time'].toDate());
              data['distance'] = (
                  (data['ra'] - ra_search)**2 +
                  (data['dec'] - dec_search)**2
              )**(0.5);

              commit('addObservationRun', data);
              commit('setFromSearch', true);
            });
          }).catch(err => {
            console.log('Error searching observations', err)
            commit('setFromSearch', false);
          }).finally(() => {
            commit('setSearching', 'observations', false);
          });
      },

      searchSources: function({ commit, state } ){
        commit('setSearching', 'picid', true);
        commit('setSources', []);
        db.collection('picid')
          .where('dec', '>=', state.searchModel.dec - state.searchModel.searchRadius)
          .where('dec', '<=', state.searchModel.dec + state.searchModel.searchRadius)
          .orderBy('dec')
          .orderBy('last_process_time', 'desc')
          .limit(500)
          .get().then(querySnapshot => {
            let rows = [];
            querySnapshot.docs.forEach((doc) => {
              let data = doc.data();
              data['picid'] = doc.id;
              if (data.ra >= state.searchModel.ra - state.searchModel.searchRadius){
                return false;
              }
              if (data.ra <= state.searchModel.ra + state.searchModel.searchRadius){
                return false;
              }

              // Todo: filter date here.
              data['time'] = moment(data['last_process_time'].toDate());
              data['distance'] = (
                  (data['ra'] - ra_search)**2 +
                  (data['dec'] - dec_search)**2
              )**(0.5);

              rows.push(data);
            });
            console.log(rows);
            commit('setSources', rows);
          }).catch(err => {
            console.log('Error searching images', err)
            commit('setFromSearch', false);
          }).finally(() => {
            commit('setSearching', 'picid', false);
          });
      }
  }
})
