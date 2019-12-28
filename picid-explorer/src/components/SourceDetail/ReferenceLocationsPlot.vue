<template>
    <div>
      <b-spinner v-if="loading" label="Loading..."></b-spinner>
      <Plotly
        :data="plotData"
        :layout="layout"
      /></Plotly>
    </div>
</template>

<script>
import { Plotly } from 'vue-plotly'
import { mapState } from 'vuex'

export default {
    components: {
        Plotly
    },
    methods: {
        loadData(data){
            this.loading = true;
            this.plotData[0]['x'] = data.x;
            this.plotData[0]['y'] = data.y;

            this.plotData[1]['x'] = data.x[0];
            this.plotData[1]['y'] = data.y[0];

            this.$nextTick();
            this.loading = false;
        }
    },
    watch: {
        locationData: function(newValue, oldValue) {
          this.loadData(newValue);
        }
    },
    computed: {
        ...mapState(['locationData']),
    },
    data () {
        return {
            name: 'ReferenceLocationsPlot',
            loading: false,
            imageTimes: [],
            layout: {
              autosize: false,
              width: 900,
              height: 600,
              title: 'Reference Locations ' + this.$route.params.picid,
              xaxis: {
                range: [ 0, 5208]
              },
              yaxis: {
                range: [0, 3476]
              },
            },
            plotData: [
              {
                x: [],
                y: [],
                mode: 'markers',
                type: 'scatter',
                name: 'References'
              },
              {
                x: [],
                y: [],
                mode: 'markers',
                type: 'scatter',
                name: 'Target',
                marker: {
                    color: 'red',
                    style: '*',
                    size: 200
                }
              }
            ]
        }
    }
}
</script>

