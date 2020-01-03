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
import { create, all } from 'mathjs'

const math = create(all)

export default {
    components: {
        Plotly
    },
    methods: {
        loadData(data){
            this.imageTimes = data.image_time;
            this.plotData[0]['x'] = data.image_time;
            this.plotData[1]['x'] = data.image_time;
            this.plotData[2]['x'] = data.image_time;

            this.plotData[0]['y'] = data.r;
            this.plotData[1]['y'] = data.g;
            this.plotData[2]['y'] = data.b;

            this.layout.shapes[0]['x0'] = [data.image_time[this.frameIndex]];
            this.layout.shapes[0]['x1'] = [data.image_time[this.frameIndex]];

            this.$nextTick();
        }
    },
    mounted: function() {
        this.loadData(this.lightcurveData);
    },
    watch: {
        lightcurveData: function(newValue, oldValue) {
            this.loadData(newValue);
        }
    },
    computed: {
      ...mapState([
        'frameIndex',
        'lightcurveData'
      ]),
      loading: function() {
        return this.imageTimes ===  [];
      }
    },
    data () {
        return {
            name: 'LightcurvePlot',
            imageTimes: [],
            layout: {
              title: 'Lightcurve ' + this.$store.state.picid,
              colors: ['red', 'green', 'blue'],
              shapes: [
                {
                  x0: [],
                  x1: [],
                  y0: [.9],
                  y1: [1.1],
                  line: {
                    color: 'rgb(55, 128, 191)',
                    width: 3
                  }
                }
              ],
            },
            plotData: [
              {
                x: [],
                y: [],
                mode: 'lines+markers',
                name: 'R data',
                line: {
                  color: 'red',
                  size: 3
                },
                marker: {
                  color: 'red',
                  size: 7
                }
              },
              {
                x: [],
                y: [],
                mode: 'lines+markers',
                name: 'G data',
                line: {
                  color: 'green',
                  size: 3
                },
                marker: {
                  color: 'green',
                  size: 7
                }
              },
              {
                x: [],
                y: [],
                mode: 'lines+markers',
                name: 'B data',
                line: {
                  color: 'blue',
                  size: 3
                },
                marker: {
                  color: 'blue',
                  size: 7
                }
              }
            ]
        }
    }
}
</script>

