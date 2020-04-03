<template>
  <v-card outlined>
    <v-card-title>
      <v-text-field v-model="search" append-icon="mdi-magnify" label="Filter Observations" single-line hide-details />
    </v-card-title>
    <v-data-table id="obsTable" v-model="selectedObservations" :dense="dense" :headers="fields" :items="state.model.observations" :items-per-page="perPage" :search="search" :loading="state.search.isSearching.observations" class="elevation-1">
      <template v-slot:item.unit_id="{ item }">
        <nuxt-link :to="'/units/' + item.unit_id">
          {{
          item.unit_id
          }}
        </nuxt-link>
      </template>
      <template v-slot:item.sequence_id="{ item }">
        <nuxt-link :to="'/observation/' + item.sequence_id">
          {{
          item.sequence_id
          }}
        </nuxt-link>
      </template>
      <template v-slot:item.ra="{ item }">{{ item.ra | roundVal }}</template>
      <template v-slot:item.dec="{ item }">{{ item.dec | roundVal }}</template>
      <template v-slot:item.time="{ item }">{{ item.time | moment('utc', 'YYYY-MM-DD HH:mm') }}</template>
      <template v-slot:item.status="{ item }">{{ item.status }}</template>
    </v-data-table>
    <!--     <v-card-actions align="right">
      <v-spacer />
      <v-btn :disabled="state.search.hasResults" small>
        <v-icon>mdi-table</v-icon>Get CSV
      </v-btn>
    </v-card-actions> -->
  </v-card>
</template>
<script>
export default {
  name: 'Observations',
  filters: {
    formatUnitId: (value) => {
      // Silly formatting
      let unitId = 'PAN000'
      const l = -1 * value.toFixed(0).length
      unitId = unitId.slice(0, l)
      unitId += value
      return unitId
    },
    roundVal: (value) => {
      return parseFloat(value).toFixed(3)
    }
  },
  props: {
    perPage: {
      type: Number,
      default: 25
    },
    dense: {
      type: Boolean,
      default: true
    }
  },
  data() {
    return {
      search: '',
      selectedObservations: [],
      allowDownloads: false,
      rows: [],
      fields: [{
          text: 'Unit',
          value: 'unit_id',
          sortable: true,
          width: '0.8rem'
        },
        {
          text: 'Observation ID',
          value: 'sequence_id',
          sortable: true
        },
        {
          text: 'Field',
          value: 'field_name',
          sortable: true
        },
        {
          text: 'RA [deg]',
          value: 'ra',
          sortable: true
        },
        {
          text: 'Dec [deg]',
          value: 'dec',
          sortable: true
        },
        {
          text: 'Exptime [sec]',
          value: 'exptime',
          sortable: true
        },
        // {
        //   text: 'Status',
        //   value: 'status',
        //   sortable: true
        // },
        {
          text: 'Date [UTC]',
          value: 'time',
          sortable: true,
          width: 200
        }
        // { text: 'Image Count', value: 'image_count', sortable: true, type: 'number' },
      ]
    }
  },
  computed: {
    state() {
      return this.$store.state
    }
  }
}

</script>
<style scoped>
a {
  color: #42b983;
}

#obsTable {
  font-family: monospace;
}

</style>
