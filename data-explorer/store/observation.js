import { Funcs } from '@/plugins/firebase'

export const state = () => ({
  observation: {
    sequence_id: null,
    unit_id: null,
    camera_id: null,
    software_version: null,
    ra: null,
    dec: null,
    exptime: null,
    status: null,
    time: null
  },
  selectedImage: [],
  images: []
})

export const mutations = {
  SET_OBSERVATION(state, obs) {
    state.observation = obs
  },
  SET_IMAGES(state, images) {
    state.images = images
  },
  SET_IMAGE(state, image) {
    state.selectedImage = [image]
  }
}

export const actions = {
  async GET_OBSERVATION({ commit }, sequence_id) {
    await Funcs.httpsCallable('getObservation')({ sequence_id: sequence_id }).then(
      async (result) => {
        await commit('SET_OBSERVATION', result.data)
      }
    )
  },
  async GET_IMAGES({ commit, state }, sequence_id) {
    await Funcs.httpsCallable('getImages')({ sequence_id: sequence_id }).then(
      async (result) => {
        await commit('SET_IMAGES', result.data)
      }
    )
  }
}
