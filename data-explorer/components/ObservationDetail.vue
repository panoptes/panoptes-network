<template>
  <v-container>
    <v-row>
      <v-col cols="8"></v-col>
      <v-col cols="4">
        <ObservationInfo />
      </v-col>
    </v-row>
    <v-row>
      <v-col cols="8">
      </v-col>
      <v-col cols="4">
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
