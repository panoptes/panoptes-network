<template>
  <div>
    <Plotly
      :data="plotData"
      :layout="layout"
    /></Plotly>
  </div>
</template>

<script>
import { mapState } from 'vuex'

import { Plotly } from 'vue-plotly'

export default {
    components: {
        Plotly
    },
    watch: {
        pixelData: function(newValue, oldValue) {
          this.loadData(newValue)
        }
    },
    methods: {
        loadData(data){
            this.plotData[0]['x'] = data.image_time
            this.plotData[1]['x'] = data.image_time

            this.plotData[0]['y'] = data.x_offset
            this.plotData[1]['y'] = data.y_offset

            this.$nextTick()
        }
    },
    computed: {
        ...mapState(['pixelData'])
    },
    data () {
        return {
            name: 'PixelDriftPlot',
            imageTimes: [],
            layout: {
              title: 'Pixel Drift ' + this.$store.state.picid
            },
            plotData: [
              {
                x: [],
                y: [],
                mode: 'lines+markers',
                name: 'X-axis'
              },
              {
                x: [],
                y: [],
                mode: 'lines+markers',
                name: 'Y-axis'
              }
            ]
        }
    }
}
</script>

