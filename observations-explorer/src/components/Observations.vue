<template>
  <div>
    <vue-good-table
      :columns="columns"
      :rows="rows"
      :pagination-options="{
        enabled: true
      }"
      :sort-options="{
        enabled: true,
        initialSortBy: {field: 'start_date', type: 'desc'}
      }"
    />
  </div>
</template>

<script>
import { VueGoodTable } from 'vue-good-table'
import 'vue-good-table/dist/vue-good-table.css'

import { ObservationsService } from '../services/ObservationsService.js'

let observations = new ObservationsService()

export default {
  name: 'Observations',
  components: {
    VueGoodTable
  },
  methods: {
    unitFormatFn: function (value) {
      // Silly formatting
      let unitId = 'PAN000'
      let l = -1 * value.toFixed(0).length
      unitId = unitId.slice(0, l)
      unitId += value
      return unitId
    }
  },
  data () {
    return {
      columns: [
        {
          label: 'PAN ID',
          field: 'unit_id',
          formatFn: this.unitFormatFn,
          width: '5%',
          filterOptions: {
            enabled: true,
            placeholder: 'PAN ID',
            filterValue: '',
            filterDropdownItems: [
              {value: 1, text: 'PAN001'},
              {value: 6, text: 'PAN006'}
            ]
          }
        },
        {
          label: 'Sequence ID',
          field: 'id',
          width: '10%',
          filterOptions: {
            enabled: true
          }
        },
        {
          label: 'Date',
          field: 'start_date',
          type: 'date',
          width: '10%',
          dateInputFormat: 'YYYY-MM-DDThh:mm:ss',
          dateOutputFormat: 'YYYY-MM-DD  HH:MM:SS'
        },
        {
          label: 'Exptime',
          field: 'exp_time',
          type: 'decimal',
          width: '5%'
        },
        {
          label: 'Images',
          field: 'image_count',
          type: 'number',
          width: '5%'
        },
        {
          label: 'POCS Version',
          field: 'pocs_version',
          width: '10%',
          filterOptions: {
            enabled: true,
            placeholder: 'Version',
            filterValue: '',
            filterDropdownItems: [
              'POCSv0.6.0',
              'POCSv0.6.1'
            ]
          }
        },
        {
          label: 'Status',
          field: 'piaa_state',
          width: '10%'
        }
      ],
      rows: observations.data
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
h1, h2 {
  font-weight: normal;
}
ul {
  list-style-type: none;
  padding: 0;
}
li {
  display: inline-block;
  margin: 0 10px;
}
a {
  color: #42b983;
}
</style>
