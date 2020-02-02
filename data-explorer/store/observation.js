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
    }
})

export const mutations = () => ({
    SET_OBSERVATION(state, obs) {
        state.observation = obs
    }
})

export const actions = {
    async GET_OBSERVATION({ commit }, sequence_id) {
        console.log('Getting observation for ' + sequence_id)
        await Funcs.httpsCallable('getObservation')({ sequence_id: sequence_id }).then(
            async (result) => {
                console.log(result.data)
                await commit('SET_OBSERVATION', result.data)
            }
        )
    }
}
