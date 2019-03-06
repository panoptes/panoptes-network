<template>
  <div>
    <vue-good-table 
      :columns="fields"
      :rows="rows"
      :pagination-options="{
        enabled: true,
        mode: 'pages',
        perPage: this.perPage
      }"
      styleClass="vgt-table striped bordered condensed"
    >
    <template slot="table-row" slot-scope="props">
      <span v-if="props.column.field == 'id'">
        <router-link 
          :to="{ name: 'observationDetail', params: { sequenceId: props.row.id, info: props.row }}">
          {{ props.row.id }}
        </router-link>
      </span>
      <span v-else>
        {{props.formattedRow[props.column.field]}}
      </span>
    </template>   
  </vue-good-table>
  </div>
</template>

<script>
import { ObservationsService } from '../services/ObservationsService.js'

let observations = new ObservationsService()

export default {
  name: 'Observations',
  components: {
  },
  methods: {
    formatUnitId: function (value) {
      // Silly formatting
      let unitId = 'PAN000'
      let l = -1 * value.toFixed(0).length
      unitId = unitId.slice(0, l)
      unitId += value
      return unitId      
    }
  },
  created () {
    this.observations.getAllObservations().then(response => {
      this.rows = response.data.items
    })
      .catch(error => {
        console.log(error)
      })
      .finally(() => (this.loading = false))
  },
  data () {
    return {
      perPage: 10,
      currentPage: 0,
      observations: observations,
      filter: null,
      rows: [],
      fields: [
        { 
          label: 'Unit', 
          field: 'unit_id', 
          sortable: true, 
          formatFn: this.formatUnitId,
          filterOptions: {
            enabled: true,
            filterDropdownItems: [
              { value: 1, text: 'PAN001' },
              { value: 6, text: 'PAN006' },
              { value: 12, text: 'PAN012' },
            ]
          }
        },
        { 
          label: 'Sequence', 
          field: 'id', 
          sortable: true,
          filterOptions: {
            enabled: true
          }
        },
        { 
          label: 'Field', 
          field: 'field', 
          sortable: true ,
          filterOptions: {
            enabled: true
          }
        },
        // { label: 'POCS Version', field: 'pocs_version', sortable: true },
        { 
          label: 'Date', 
          field: 'start_date', 
          sortable: true, 
          type: 'date',
          type: 'date',
          dateInputFormat: 'YYYY-MM-DDTHH:mm:ss',
          dateOutputFormat: 'YYYY-MM-DD HH:mm',
          filterOptions: {
            enabled: true
          }    
        },
        { label: 'Exp Time', field: 'exptime', sortable: true, type: 'decimal' },
        { label: 'Image Count', field: 'image_count', sortable: true, type: 'number' },
        // { label: 'Status', field: 'piaa_state', sortable: true }
      ]
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
a {
  color: #42b983;
}
</style>
