import { DB } from '@/plugins/firebase'

export const state = () => ({
  units: [],
  selectedUnit: null
})

export const mutations = {
  SET_UNITS(state, units) {
    state.units = units
  },
  SET_UNIT(state, unit) {
    state.selectedUnit = unit
  }
}

export const actions = {
  async GET_UNITS({ commit, state }, unit_id) {
    if (state.units.length == 0) {
      return DB.collection('units')
        .limit(100)
        .onSnapshot(async function (querySnapshot) {
          var units = []
          querySnapshot.forEach(async function (doc) {
            const data = doc.data()
            data['unit_id'] = doc.id
            units.push(data)
            // If we have a single unit selected.
            if (doc.id == unit_id) {
              await commit('SET_UNIT', data)
            }
          })
          return await commit('SET_UNITS', units)
        })
    } else {
      state.units.forEach(async function(unit) {
        if (unit.unit_id == unit_id) {
          await commit('SET_UNIT', unit)
        }
      })
    }
  }
}
