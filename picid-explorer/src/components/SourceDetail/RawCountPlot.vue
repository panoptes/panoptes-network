<template>
    <div>
      <b-spinner v-if="loading" label="Loading..."></b-spinner>
      <Plotly
        v-if="!loading"
        :data="plotData"
        :layout="layout"
      /></Plotly>
    </div>
</template>

<script>
import { mapState, mapActions } from 'vuex'

import { Plotly } from 'vue-plotly'

export default {
    components: {
        Plotly
    },
    methods: {
        loadData(data){
            this.plotData[0]['x'] = data.image_time;
            this.plotData[1]['x'] = data.image_time;
            this.plotData[2]['x'] = data.image_time;

            this.plotData[0]['y'] = data.flux_best;
            this.plotData[1]['y'] = data.reference;
            this.plotData[2]['y'] = data.target;

            this.$nextTick();
            this.loading = false;
        }
    },
    watch: {
        rawData: function(newValue, oldValue) {
          this.loadData(newValue);
        }
    },
    computed: {
        ...mapState(['rawData'])
    },
    data () {
        return {
            name: 'RawCountPlot',
            loading: true,
            imageTimes: [],
            layout: {
              title: 'Raw Counts ' + this.$store.state.picid
            },
            plotData: [
              {
                x: [],
                y: [],
                mode: 'lines+markers',
                name: 'Source extractor'
              },
              {
                x: [],
                y: [],
                mode: 'lines+markers',
                name: 'Reference'
              },
              {
                x: [],
                y: [],
                mode: 'lines+markers',
                name: 'Target'
              }
            ]
        }
    }
}
</script>

