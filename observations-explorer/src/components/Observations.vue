<template>
  <div>
    <b-table 
      :items="rows" 
      :fields="fields"
      :per-page="perPage"
      :current-page="currentPage"
      sort-by="start_date"
      :sort-desc=true
      striped
      hover
      bordered
      outlined
      responsive
      small
    >
    <template slot="id" slot-scope="data">
      <router-link 
        :to="{ name: 'observationDetail', params: { sequenceId: data.value, info: data.item }}">
        {{ data.value }}
      </router-link>
    </template>    
    </b-table>
    <b-row>
      <b-col cols="3">
        <b-pagination :total-rows="rows.length" :per-page="perPage" v-model="currentPage" class="my-0" />
      </b-col>
    </b-row>
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
      rows: [],
      fields: [
        { label: 'Unit', key: 'unit_id', sortable: true, formatter: this.unitId },
        { label: 'Sequence', key: 'id', sortable: true },
        { label: 'Field', key: 'field', sortable: true },
        { label: 'POCS Version', key: 'pocs_version', sortable: true },
        { label: 'Date', key: 'start_date', sortable: true },
        { label: 'Exp Time', key: 'exp_time', sortable: true },
        { label: 'Image Count', key: 'image_count', sortable: true },
        { label: 'Status', key: 'piaa_state', sortable: true }
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
