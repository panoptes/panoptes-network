import { Funcs } from '@/plugins/firebase'

export const state = () => ({
  units: [],
  observations: [],
  lightcurves: []
})

export const mutations = {
  SET_RECENT_OBS(state, records) {
    state.observations = records
  },
  SET_RECENT_LIGHTCURVES(state, records) {
    state.lightcurves = records
  }
}

export const actions = {
  async GET_RECENT({ dispatch }) {
    await Promise.all([
      dispatch('GET_RECENT_OBS'),
      dispatch('GET_RECENT_LIGHTCURVES')
    ])
  },
  async GET_RECENT_OBS({ commit }) {
    // console.log('Getting recent obs')
    // await commit('SET_RECENT_OBS', [])
    await Funcs.httpsCallable('getRecentObservations')({ limit: 50 }).then(
      async (result) => {
        // console.log(result.data)
        await commit('SET_RECENT_OBS', result.data)
      }
    )
  },
  async GET_RECENT_LIGHTCURVES({ commit }) {
    // console.log('Getting recent lightcurves')
    await commit('SET_RECENT_LIGHTCURVES', [])
  }
}
