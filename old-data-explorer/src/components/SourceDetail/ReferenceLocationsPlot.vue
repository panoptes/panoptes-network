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
        locationData: function(newValue, oldValue) {
          this.loadData(newValue)
        }
    },
    methods: {
        loadData(data){
          if (data.x !== undefined){
            this.plotData[0]['x'] = data.x
            this.plotData[0]['y'] = data.y
            this.plotData[0].marker.color = data.score_rank

            for (var i = data.x.length - 1; i >= 0; i--) {
              let labelText = 'Score Rank: ' + data.score_rank[i]
              labelText += '<br />'
              labelText += 'Score (x100): ' + (data.score[i] * 100).toFixed(3)
              labelText += '<br />'
              labelText += 'Coeff: ' + data.coeffs[i].toFixed(3)
              this.plotData[0].text.push(labelText)

              // let markerSize = 1 / (data.score_rank[i] / 80);
              // this.plotData[0].marker.size.push(markerSize);
            }

            this.plotData[1]['x'] = [data.x[0]]
            this.plotData[1]['y'] = [data.y[0]]

            this.$nextTick()
          }
        }
    },
    computed: {
      ...mapState([
        'picid',
        'locationData'
      ])
    },
    data () {
        return {
            name: 'ReferenceLocationsPlot',
            imageTimes: [],
            layout: {
              autosize: false,
              width: 900,
              height: 600,
              title: 'Reference Locations ' + this.$store.state.picid,
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
                name: 'References',
                text: [],
                marker: {
                  colorscale: 'Picnic',
                  symbol: 'star',
                  size: 11
                }
              },
              {
                x: [],
                y: [],
                mode: 'markers',
                type: 'scatter',
                name: 'Target',
                marker: {
                    color: 'red',
                    symbol: 'star',
                    size: 19,
                    line: {
                      color: 'black',
                      width: 2
                    }
                }
              }
            ]
        }
    }
}
</script>

