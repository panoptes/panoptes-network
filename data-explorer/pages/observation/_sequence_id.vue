<template>
  <v-container fluid>
    <v-row dense>
      <v-col cols="3">
        <ObservationInfo />
      </v-col>
      <v-col cols="6">
        <v-tabs grow>
          <v-tab>Plots</v-tab>
          <v-tab>Links</v-tab>
          <v-tab-item>
            <ObservationPlot />
          </v-tab-item>
          <v-tab-item>Links here</v-tab-item>
        </v-tabs>
      </v-col>
      <v-col cols="3">
        <ImageList />
      </v-col>
    </v-row>
  </v-container>
</template>
<script>
import ObservationInfo from '@/components/Observation/ObservationInfo'
import ObservationPlot from '@/components/Observation/ObservationPlot'
import ImageList from '@/components/Observation/ImageList'

export default {
  name: 'Observation',
  components: {
    ObservationInfo,
    ObservationPlot,
    ImageList
  },
  async fetch({ store, params }) {
    await store.dispatch('observation/GET_OBSERVATION', params.sequence_id)
    await store.dispatch('observation/GET_IMAGES', params.sequence_id)
  }
}

</script>
