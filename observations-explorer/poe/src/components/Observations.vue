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
      :theme="nocturnal"
    />
  </div>
</template>

<script>
import { VueGoodTable } from 'vue-good-table'
import 'vue-good-table/dist/vue-good-table.css'

import observations from '../assets/observations.json'

export default {
  name: 'Observations',
  observations_data: observations,
  components: {
    VueGoodTable
  },
  methods: {
    unitFormatFn: function (value) {
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
          label: 'Unit',
          field: 'unit_id',
          formatFn: this.unitFormatFn,
          filterOptions: {
            enabled: true,
            placeholder: 'Filter Unit',
            filterValue: '',
            filterDropdownItems: [
              {value: 1, text: 'PAN001'},
              {value: 6, text: 'PAN006'}
            ]
          }
        },
        {
          label: 'Sequence',
          field: 'id',
          filterOptions: {
            enabled: true
          }
        },
        {
          label: 'Date',
          field: 'start_date',
          type: 'date',
          dateInputFormat: 'YYYY-MM-DDThh:mm:ss',
          dateOutputFormat: 'YYYY-MM-DD  HH:MM:SS'
        },
        {
          label: 'Exposure Time',
          field: 'exp_time',
          type: 'decimal'
        },
        {
          label: 'Images',
          field: 'image_count',
          type: 'number'
        },
        {
          label: 'POCS Version',
          field: 'pocs_version',
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
          field: 'piaa_state'
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
