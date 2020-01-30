import * as functions from 'firebase-functions'

if (location.hostname === 'localhost') {
  console.log('Localhost detected')
  functions.useFunctionsEmulator('http://localhost:5001')
}

export const state = () => ({
  units: [],
  observations: [],
  lightcurves: []
})

export const mutations = {
  SET_RECENT_OBS({ state }, records) {
    state.observations = records
  }
}

export const actions = {
  async GET_RECENT({ dispatch, commit }) {
    console.log('in GET_RECENT')
    await dispatch('GET_RECENT_OBS')
  },
  async GET_RECENT_OBS({ commit }) {
    console.log('Getting recent obs')

    await functions
      .httpsCallable('getRecentObservations')({
        limit: 25
      })
      .then(async (result) => {
        await commit('SET_RECENT_OBS', result.data)
      })
      .catch((err) => {
        console.error(err)
      })
  }
}
