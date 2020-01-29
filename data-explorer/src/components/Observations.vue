<template>
 <v-card outlined>
    <v-card-title>
      <v-text-field
        v-model="search"
        append-icon="mdi-magnify"
        label="Filter Observations"
        single-line
        hide-details
      ></v-text-field>
    </v-card-title>

    <v-data-table
      id="obsTable"
      :dense="dense"
      :headers="fields"
      :items="observations"
      :items-per-page="perPage"
      :search="search"
      :loading="isSearching"
      v-model="selectedObservations"
      order-by="time"
      class="elevation-1"
    >
      <template v-slot:item.sequence_id="{ item }">
        <router-link
          :to="{ name: 'observationDetail', params: { sequenceId: item.sequence_id }}">
          {{ item.sequence_id }}
        </router-link>
      </template>
      <template v-slot:item.ra="{ item }">
          {{ item.ra | roundVal }}
      </template>
      <template v-slot:item.dec="{ item }">
          {{ item.dec | roundVal }}
      </template>
      <template v-slot:item.time="{ item }">
          {{ item.time | moment('utc', 'YYYY-MM-DD HH:mm:ss') }}
      </template>
      <template v-slot:item.status="{ item }">
          {{ item.status }}
      </template>      
    </v-data-table>

    <v-card-actions align="right" v-if="allowDownloads">
      <v-spacer></v-spacer>
      <v-btn small :disabled="!selectedObservations.length">
        <v-icon>mdi-table</v-icon> Get CSV
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script>
import { mapState, mapActions } from 'vuex'

export default {
  name: 'Observations',
  filters: {
    formatUnitId: function (value) {
      // Silly formatting
      let unitId = 'PAN000'
      let l = -1 * value.toFixed(0).length
      unitId = unitId.slice(0, l)
      unitId += value
      return unitId
    },
    roundVal: function(value) {
      return parseFloat(value).toFixed(3);
    }
  },
  computed: {
    ...mapState([
      'units',
      'searchModel',
      'observations',
    ]),
    isSearching: function() {
      return this.searchModel.isSearching['observations'];
    }
  },
  props: [
    'perPage',
    'dense'
  ],
  data () {
    return {
      search: '',
      selectedObservations: [],
      allowDownloads: false,
      rows: [],
      fields: [
        {
          text: 'Unit',
          value: 'unit_id',
          sortable: true,
        },
        {
          text: 'Sequence',
          value: 'sequence_id',
          sortable: true,
        },
        {
          text: 'Field',
          value: 'field_name',
          sortable: true ,
        },
        {
          text: 'RA [deg]',
          value: 'ra',
          sortable: true ,
        },
        {
          text: 'Dec [deg]',
          value: 'dec',
          sortable: true ,
        },
        {
          text: 'Date [UTC]',
          value: 'time',
          sortable: true,
        },
        {
          text: 'Exptime [sec]',
          value: 'exptime',
          sortable: true
        },
        {
          text: 'Status',
          value: 'status',
          sortable: true
        },
        // { text: 'Image Count', value: 'image_count', sortable: true, type: 'number' },
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
#obsTable {
  font-family: monospace
}
</style>
