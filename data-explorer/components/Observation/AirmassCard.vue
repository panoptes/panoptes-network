<template>
  <v-card class="mx-auto" color="grey lighten-4" width="200" height="100">
    <v-card-title>
      <v-row align="start">
        <div class="caption text-uppercase">{{ metricName }}</div>
        <div>
          <span class="display-2 font-weight-black" v-text="avg.toFixed(2) || '—'"></span>
          <strong v-if="avg">{{ metricUnit }}</strong>
        </div>
      </v-row>
    </v-card-title>

    <v-sheet v-if="showSparkline" color="transparent">
      <v-sparkline
        :key="String(avg)"
        :smooth="16"
        :gradient="['blue']"
        :line-width="3"
        :value="airmass"
        auto-draw
        stroke-linecap="round"
      ></v-sparkline>
    </v-sheet>
  </v-card>
</template>

<script>
export default {
  computed: {
    avg() {
      const sum = this.airmass.reduce((acc, cur) => acc + cur, 0)
      const length = this.airmass.length

      if (!sum && !length) return 0

      return sum / length
    },
    airmass: function() {
      const airmassList = []
      this.$store.state.observation.images.forEach((img) => {
        airmassList.push(img.airmass)
      })
      return airmassList
    },
    imgTimes: function() {
      const timeList = []
      this.$store.state.observation.images.forEach((img) => {
        timeList.push(img.time)
      })
      return timeList
    }
  },
  props: {
      showSparkline: {
          type: Boolean,
          default: false
      }
  },
  data() {
    return {
      metricName: 'airmass',
      metricUnit: ''
    }
  }
}
</script>

<style>
.v-sheet--offset {
  top: -24px;
  position: relative;
}
</style>