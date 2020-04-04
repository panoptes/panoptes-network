<template>
  <v-card class="mx-auto">
    <div id="plotBoard" v-if="background_info"></div>
  </v-card>
</template>
<script>
import { default as vegaEmbed } from 'vega-embed'

export default {
  computed: {
    background_info: function() {
      const bgList = []
      this.$store.state.observations.images.forEach(img => {
        bgList.push(
          {
            time: img.time,
            rms: img.background.rms.r,
            background: img.background.median.r,
            color: 'red'
          },
          {
            time: img.time,
            rms: img.background.rms.g,
            background: img.background.median.g,
            color: 'green'
          },
          {
            time: img.time,
            rms: img.background.rms.b,
            background: img.background.median.b,
            color: 'blue'
          }
        )
      })
      return bgList
    }
  },
  mounted: function() {
    this.$nextTick(function() {
      this.spec.datasets.background = this.background_info
      this.spec.datasets.selectedImage = this.$store.state.observations.selectedImage
      // vegaEmbed('#plotBoard', this.spec)
    })
  },
  data() {
    return {
      spec: {
        $schema: 'https://vega.github.io/schema/vega-lite/v4.0.2.json',
        datasets: {
          background: [],
          selectedImage: []
        },
        data: { name: 'background' },
        width: 600,
        height: 250,
        autosize: { type: 'fit', contains: 'padding' },
        layer: [
          {
            encoding: {
              color: {
                field: 'color',
                type: 'nominal',
                scale: { range: ['blue', 'green', 'red'] }
              },
              x: { field: 'time', title: 'Time [UTC]', type: 'temporal' },
              y: {
                field: 'background',
                scale: { zero: false },
                title: 'Counts [ADU]',
                type: 'quantitative'
              }
            },
            mark: { type: 'line', point: true },
            title: 'Background'
          },
          {
            encoding: {
              color: {
                field: 'color',
                scale: { range: ['blue', 'green', 'red'] },
                type: 'nominal'
              },
              x: { field: 'time', type: 'temporal' },
              y: { field: 'ymin', title: '', type: 'quantitative' },
              y2: { field: 'ymax' }
            },
            mark: 'errorbar',
            transform: [
              { as: 'ymin', calculate: 'datum.background-datum.rms' },
              { as: 'ymax', calculate: 'datum.background+datum.rms' }
            ]
          },
          {
            data: { name: 'selectedImage' },
            encoding: { x: { field: 'time', type: 'temporal' } },
            mark: { strokeWidth: 2, type: 'rule' }
          }
        ]
      }
    }
  }
}
</script>
