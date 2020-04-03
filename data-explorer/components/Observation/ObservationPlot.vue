<template>
  <v-row>
    <v-col cols="12">
      <div id="plotBoard">
      </div>
        <code>{{ background_info }}</code>
    </v-col>
  </v-row>
</template>
<script>
import { default as vegaEmbed } from 'vega-embed'

export default {
  computed: {
    observation: function() {
      return this.$store.state.observation.observation
    },
    background_info: function() {
      const bgList = []
      this.$store.state.observation.images.forEach(img => {
        bgList.push(
          { time: img.time, rms: img.background.rms.r, background: img.background.median.r, color: 'red' },
          { time: img.time, rms: img.background.rms.g, background: img.background.median.g, color: 'green' },
          { time: img.time, rms: img.background.rms.b, background: img.background.median.b, color: 'blue' },
        )
      })
      return bgList
    }
  },
  mounted: function() {
    this.$nextTick(function() {
      vegaEmbed('#plotBoard', this.spec, { theme: 'quartz' })
    })
  },
  data() {
    return {
      spec: {
        $schema: 'https://vega.github.io/schema/vega-lite/v4.0.2.json',
        config: { view: { continuousHeight: 300, continuousWidth: 400 } },
        height: 300,
        layer: [{
            data: { values: this.background_info },
            encoding: {
              color: 'color:N',
              x: { 'field': 'time', 'title': 'Time [UTC]', 'type': 'temporal' },
              y: {
                field: 'background',
                scale: { zero: false },
                title: 'Counts [ADU]',
                type: 'quantitative'
              }
            },
            mark: 'line',
            title: 'Background'
          },
          {
            data: { values: this.background_info },
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
            title: 'Background',
            transform: [{ as: 'ymin', calculate: 'datum.background-datum.rms' },
              { as: 'ymax', calculate: 'datum.background+datum.rms' }
            ]
          }
        ],
        width: 600
      }

    }
  }
}

</script>
