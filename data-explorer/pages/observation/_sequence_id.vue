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
          <v-tab-item>
            <LinkList />
          </v-tab-item>
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
import LinkList from '@/components/Observation/LinkList'

export default {
  name: 'Observation',
  components: {
    ObservationInfo,
    ObservationPlot,
    ImageList,
    LinkList
  },
  async fetch({ store, params }) {
    await store.dispatch('observations/GET_OBSERVATION', params.sequence_id)
    await store.dispatch('observations/GET_IMAGES', params.sequence_id)
  }
}

</script>
