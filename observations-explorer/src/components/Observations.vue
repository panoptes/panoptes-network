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
    >
    <template slot="table-row" slot-scope="props">
      <span v-if="props.column.field == 'id'">
        <a v-bind:href="'/observations/' + props.row.id">
          {{props.row.id}}
        </a>
      </span>
      <span v-else>
        {{props.formattedRow[props.column.field]}}
      </span>
    </template>
    </vue-good-table>
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
    },
    sequenceFormatFn: function (value) {
      let link = '<a href="observations/' + value + '>' + value + '</a>'
      return link
    }
  },
  created () {
    this.observations.getObservations().then(response => {
      this.rows = response.data.data
    })
      .catch(error => {
        console.log(error)
      })
      .finally(() => (this.loading = false))
  },
  data () {
    return {
      observations: observations,
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
          dateInputFormat: 'YYYY-MM-DDTHH:mm:ss',
          dateOutputFormat: 'YYYY-MM-DD HH:mm:ss'
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
