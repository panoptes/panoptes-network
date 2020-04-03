<template>
  <v-row dense>
    <v-col cols="3">
      <UnitInfo :unit="unit" v-if="unit"/>
    </v-col>
  </v-row>
</template>

<script>
import { mapMutations } from 'vuex'
import UnitInfo from '@/components/Unit'

export default {
  name: 'UnitInfoPage',
  computed: {
    unit: function() {
      return this.$store.state.unit.selectedUnit
    }
  },
  components: {
    UnitInfo
  },
  mounted: function() {
    this.$nextTick(function() {
    })
  },
  data: () => ({}),
  async fetch({ store, params }) {
    await store.dispatch('unit/GET_UNITS', params.unit_id)
  }
}

</script>
