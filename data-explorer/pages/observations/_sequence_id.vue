<template>
  <v-container flex>
    <v-row no-gutters>
      <v-col>
        <ObservationDetail />
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import ObservationDetail from '@/components/ObservationDetail'

export default {
  name: 'Observation',
  components: {
    ObservationDetail
  },
  async fetch({ store, params }) {
    await store.dispatch('observation/GET_OBSERVATION', params.sequence_id)
    await store.dispatch('observation/GET_IMAGES', params.sequence_id)
  }
}
</script>
