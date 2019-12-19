<template>
    <div>
        <b-spinner v-if="loading" label="Loading..."></b-spinner>
        {{ r_std }}
      <Plotly
        v-if="!loading"
        :data="plotData"
        :layout="layout"
      /></Plotly>
    </div>
</template>

<script>
import { Plotly } from 'vue-plotly'
import { create, all } from 'mathjs'

const math = create(all)

export default {
    name: 'lightcurve-plot',
    components: {
        Plotly
    },
    props: {
        stampData: {
            type: Object,
            required: true
        },
        loading: {
            type: Boolean,
            default: true
        }
    },
    methods: {
        loadData(data){
            this.plotData[0]['x'] = data.image_time;
            this.plotData[1]['x'] = data.image_time;
            this.plotData[2]['x'] = data.image_time;

            this.plotData[0]['y'] = data.r;
            this.plotData[1]['y'] = data.g;
            this.plotData[2]['y'] = data.b;

            this.$nextTick();
        }
    },
    computed: {
        r_std: function () {
            return ''; //math.std(this.plotData[0].get_y());
        }
    },
    mounted: function() {
        this.loadData(this.stampData);
    },
    watch: {
        stampData: function(newValue, oldValue) {
            this.loadData(newValue);
        }
    },
    data () {
        return {
            name: 'LightcurvePlot',
            imageTimes: [],
            layout: {
              title: 'Lightcurve ' + this.$route.params.picid,
              colors: ['red', 'green', 'blue']
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
              },
            ]
        }
    }
}
</script>

