<template>
    <div>
      Frame {{ frameIndex }}
      Total {{ totalFrames }}
      <Plotly
        :data="plotData"
        :layout="layout"
        :loading="loading"
      /></Plotly>
      <b-pagination
        :total="totalFrames"
        :current.sync="currentFrame"
        per-page="1"
      >
    </b-pagination>
    </div>
</template>

<script>
import { mapState } from 'vuex'

import { Plotly } from 'vue-plotly'

export default {
    components: {
        Plotly
    },
    methods: {
        updatePlot(){
          if (this.stampData && this.stampData.target) {
            this.plotData[0].z = this.stampData.target[this.frameIndex];
            this.layout.title = 'Frame: ' + this.frameIndex;
            this.loading = false;
          }
        }
    },
    watch: {
        stampData: function(newValue, oldValue) {
          // Start at first frame on load.
          this.updatePlot();
        },
        currentFrame: function(newValue, oldValue) {
          this.loading = true;
          this.$store.dispatch('setFrame', newValue).then(() => {
            this.updatePlot();
          });
        }
    },
    computed: {
      ...mapState([
        'picid',
        'frameIndex',
        'totalFrames',
        'stampData'
      ])
    },
    data () {
        return {
            name: 'PSCPlot',
            imageTimes: [],
            currentFrame: 0,
            loading: true,
            layout: {
              title: 'Postage Stamp Cube'
            },
            plotData: [
              {
                z: [],
                type: 'heatmap',
              }
            ]
        }
    }
}
</script>

