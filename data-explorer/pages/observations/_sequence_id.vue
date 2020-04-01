<template>
  <v-layout column justify-center align-center>
    <v-flex xs12 sm8 md6>
      <ObservationDetail />
    </v-flex>
  </v-layout>
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
