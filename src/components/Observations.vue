<template>
 <v-card>
    <v-card-title>
      <v-text-field
        v-model="search"
        append-icon="mdi-magnify"
        label="Search"
        single-line
        hide-details
      ></v-text-field>
    </v-card-title>
    <v-data-table
      :headers="fields"
      :items="rows"
      :items-per-page="10"
      :search="search"
      class="elevation-1"
    >
    <template v-slot:item.unit_id="{ item }">
      <!-- <router-link :to="{ name: 'unitDetail', params: { unitId: item.unit_id }}"> -->
        {{ item.unit_id | formatUnitId }}
      <!-- </router-link> -->
    </template>
    <template v-slot:item.id="{ item }">
      <router-link
        :to="{ name: 'observationDetail', params: { sequenceId: item.id }}">
        {{ item.id }}
      </router-link>
    </template>
    </v-data-table>
  </v-card>
</template>

<script>
import { ObservationsService } from '../services/ObservationsService.js'

let observations = new ObservationsService()

export default {
  name: 'Observations',
  components: {
  },
  filters: {
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
      search: '',
      perPage: 10,
      currentPage: 0,
      observations: observations,
      rows: [],
      fields: [
        {
          text: 'Unit',
          value: 'unit_id',
          sortable: true,
        },
        {
          text: 'Sequence',
          value: 'id',
          sortable: true,
        },
        {
          text: 'Field',
          value: 'field',
          sortable: true ,
        },
        {
          text: 'Date',
          value: 'start_date',
          sortable: true,
        },
        { text: 'Exp Time', value: 'exptime', sortable: true, type: 'decimal' },
        { text: 'Image Count', value: 'image_count', sortable: true, type: 'number' },
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
