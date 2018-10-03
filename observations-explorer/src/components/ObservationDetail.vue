<template>
  <div>
    <h2>{{ $route.params.id }}</h2>
    <vue-good-table
      :columns="columns"
      :rows="rows"
      :line-numbers="true"
      :pagination-options="{
        enabled: true
      }"
      :sort-options="{
        enabled: true,
        initialSortBy: {field: 'start_date', type: 'desc'}
      }"
    >
    </vue-good-table>
  </div>
</template>

<script>
import { VueGoodTable } from 'vue-good-table'
import 'vue-good-table/dist/vue-good-table.css'

import { ObservationsService } from '../services/ObservationsService.js'
let observations = new ObservationsService()

export default {
  name: 'ObservationDetail',
  components: {
    VueGoodTable
  },
  methods: {
    formatImagelink: function (value) {
      return value
    }
  },
  created () {
    this.observations.getObservation(this.$route.params.id).then(response => {
      this.rows = response.data.data
    })
      .catch(error => {
        console.log(error)
      })
      .finally(() => (this.loading = false))
  },
  data () {
    return {
      info: null,
      observations: observations,
      columns: [
        {
          label: 'Time',
          field: 'date_obs',
          type: 'date',
          dateInputFormat: 'YYYY-MM-DDTHH:mm:ss',
          dateOutputFormat: 'MM-DD HH:mm:ss'
        },
        { label: 'RA', field: 'center_ra', type: 'number' },
        { label: 'Dec', field: 'center_dec', type: 'number' },
        { label: 'Moon Frac', field: 'moon_fraction', type: 'number' },
        { label: 'Moon Sep', field: 'moon_separation', type: 'number' },
        {
          label: 'Image',
          field: 'id',
          formatFn: this.formatImagelink
        }
      ],
      rows: []
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
h1, h2 {
  font-weight: normal;
}
a {
  color: #42b983;
}
</style>
