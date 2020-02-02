<template>
  <v-layout>
    <v-flex class="text-center">
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
    console.log(params)
    await store.dispatch('observation/GET_OBSERVATION', params.sequence_id)
  }  
}
</script>
