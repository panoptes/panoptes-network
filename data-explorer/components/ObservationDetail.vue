<template>
  <v-container fluid>
    <v-row
      dense
      >
      <v-col cols="3">
        <ObservationInfo />
      </v-col>
      <v-col cols="6">
        Plots here.
      </v-col>
      <v-col cols="3">
        <ImageList />
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import ObservationInfo from '@/components/Observation/ObservationInfo'
import ImageList from '@/components/Observation/ImageList'

export default {
  name: 'ObservationDetail',
  components: { ObservationInfo, ImageList },
  computed: {
    observation: function() {
      return this.$store.state.observation.observation
    },
    airmass: function() {
      const airmassList = []
      this.$store.state.observation.images.forEach(img => {
        airmassList.push(img.airmass)
      })
      return airmassList
    },
    exptimes: function() {
      const timeList = []
      this.$store.state.observation.images.forEach(img => {
        timeList.push(img.exptime)
      })
      return timeList
    },
    moonfracs: function() {
      const moonList = []
      this.$store.state.observation.images.forEach(img => {
        moonList.push(img.moonfrac)
      })
      return moonList
    },
    moonseps: function() {
      const moonList = []
      this.$store.state.observation.images.forEach(img => {
        moonList.push(img.moonsep)
      })
      return moonList
    }
  },
  data() {
    return {}
  }
}
</script>
