<template>
    <div>
        <b-spinner v-if="loading" label="Loading..."></b-spinner>
      <Plotly
        v-if="!loading"
        :data="stampData"
        :layout="layout"
      /></Plotly>
    </div>
</template>

<script>
import { Plotly } from 'vue-plotly'

const csv = require('csvtojson');
const request = require('request');

export default {
    components: {
        Plotly
    },
    props: {
        sourceRunDetail: {
            type: Object,
            required: true
        }
    },
    methods: {
    },
    created: function() {
        var image_times = [];
        var r_data = [];
        var g_data = [];
        var b_data = [];

        console.log('Fetching data.')
        csv()
        .fromStream(request.get(this.sourceRunDetail.files['lightcurve-data']))
        .subscribe((json)=>{

            image_times.push(json.image_time);
            r_data.push(json.r);
            g_data.push(json.g);
            b_data.push(json.b);
        });

        console.log('Loading data.')

        this.stampData[0]['x'] = image_times;
        this.stampData[1]['x'] = image_times;
        this.stampData[2]['x'] = image_times;

        this.stampData[0]['y'] = r_data;
        this.stampData[1]['y'] = g_data;
        this.stampData[2]['y'] = b_data;

        console.log(this.stampData);
        this.loading = false;
    },
    data () {
        return {
            name: 'LightcurvePlot',
            loading: true,
            layout: {
              title: 'Lightcurve ' + this.$route.params.picid,
              colors: ['red', 'green', 'blue']
            },
            stampData: [
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

