<template>
  <div class="container">
    <b-table 
      :data="rows" 
      :bordered="true"
      :paginated="true"
      :paginationSimple="true"
      :striped="true"
      :narrowed="true"
      :hoverable="true"
      default-sort="date_obs"
    >
      <template slot-scope="props">
          <b-table-column field="unit_id" label="Unit ID" sortable>
              {{ props.row.unit_id | unitId }}
          </b-table-column>

          <b-table-column field="start_date" label="Date" sortable date>
            {{ new Date(props.row.start_date) | moment("YYYY-MM-DD hh:mm:ss") }}
          </b-table-column>

          <b-table-column field="id" label="Seq ID" sortable>
              <router-link :to="{ name: 'observationDetail', params: { sequenceId: props.row.id }}">
                {{ props.row.id}}
              </router-link>
          </b-table-column>

          <b-table-column field="field" label="Field" sortable>
              {{ props.row.field }}
          </b-table-column>     

          <b-table-column field="pocs_version" label="POCS" sortable>
              {{ props.row.pocs_version }}
          </b-table-column>                

          <b-table-column field="exp_time" label="Exptime" numeric>
              {{ props.row.exp_time }}
          </b-table-column>                

          <b-table-column field="image_count" label="Images" sortable numeric>
              {{ props.row.image_count }}
          </b-table-column>

          <b-table-column field="piaa_state" label="Status" sortable>
              {{ props.row.piaa_state }}
          </b-table-column>     
      </template>        
    </b-table>

  </div>
</template>

<script>
import { VueGoodTable } from 'vue-good-table'

import { ObservationsService } from '../services/ObservationsService.js'

let observations = new ObservationsService()

export default {
  name: 'Observations',
  components: {
    VueGoodTable
  },
  methods: {
  },
  filters: {
    unitId: function (value) {
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
      rows: []
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
