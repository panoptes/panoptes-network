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
import { Plotly } from 'vue-plotly'

export default {
    components: {
        Plotly
    },
    props: {
        pixelData: {
            type: Object,
            required: true
        }
    },
    methods: {
        loadData(data){
            this.plotData[0]['x'] = data.image_time;
            this.plotData[1]['x'] = data.image_time;

            this.plotData[0]['y'] = data.x_offset;
            this.plotData[1]['y'] = data.y_offset;

            this.$nextTick();
            this.loading = false;
        }
    },
    mounted: function() {
        this.loadData(this.pixelData);
    },
    watch: {
        pixelData: function(newValue, oldValue) {
          this.loadData(newValue);
        }
    },
    data () {
        return {
            name: 'PixelDriftPlot',
            loading: true,
            imageTimes: [],
            layout: {
              title: 'Pixel Drift ' + this.$route.params.picid
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

