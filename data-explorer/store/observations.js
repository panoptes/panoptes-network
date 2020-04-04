import { formatFirestoreRow } from '@/store/index'
import { DB } from '@/plugins/firebase'

export const state = () => ({
  observations: [],
  images: [],
  selectedObservation: [],
  selectedImage: [],
  isSearching: false
})

export const mutations = {
  SET_OBSERVATIONS(state, observations) {
    state.observations = observations
  },
  SET_OBSERVATION(state, obs) {
    state.selectedObservation = obs
  },
  SET_IMAGES(state, images) {
    state.images = images
  },
  SET_IMAGE(state, image) {
    state.selectedImage = [image]
  },
  SET_SEARCHING(state, newState) {
    state.isSearching = newState
  }
}

export const actions = {
  async GET_RECENT({ commit, state }) {
    await commit('SET_SEARCHING', true)
    if (state.observations.length == 0) {
      return DB.collection('observations')
        .orderBy('processed_time', 'desc')
        .limit(100)
        .onSnapshot(async function (querySnapshot) {
          var obs = []
          querySnapshot.forEach(async function (doc) {
            const data = doc.data()
            data['sequence_id'] = doc.id
            obs.push(formatFirestoreRow(data))
          })
          await commit('SET_OBSERVATIONS', obs)
          await commit('SET_SEARCHING', false)
        })
    }
  },
  async GET_OBSERVATION({ commit }, sequence_id) {
    return DB.doc('observations/' + sequence_id).onSnapshot(async (doc) => {
      const data = doc.data()
      data['sequence_id'] = sequence_id
      return await commit('SET_OBSERVATION', formatFirestoreRow(data))
    });
  },
  async GET_IMAGES({ commit }, sequence_id) {
    return DB.collection('images').where('sequence_id', '==', sequence_id)
    .get()
    .then(async (querySnapshot) => {
        const images = []
        querySnapshot.forEach(async (doc) => {
          const data = doc.data()
          data['image_id'] = doc.id

          images.push(formatFirestoreRow(data))
        });
        await commit('SET_IMAGES', images)
      })
      .catch(async (error) => {
        console.log("Error getting images: ", error);
        await commit('SET_IMAGES', [])
    });
  }
}
