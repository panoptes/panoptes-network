<template>
  <v-card outlined>
    <v-card-title>
      <v-text-field
        v-model="search"
        append-icon="mdi-magnify"
        label="Filter Observations"
        single-line
        hide-details
      />
    </v-card-title>

    <v-data-table
      id="obsTable"
      v-model="selectedObservations"
      :dense="dense"
      :headers="fields"
      :items="observations"
      :items-per-page="perPage"
      :search="search"
      :loading="isSearching"
      order-by="time"
      class="elevation-1"
    >
      <template v-slot:item.sequence_id="{ item }">
        <nuxt-link :to="'/observations/' + item.sequence_id">
          {{ item.sequence_id }}
        </nuxt-link>
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
    <v-card-actions align="right">
      <v-spacer />
      <v-btn :disabled="!selectedObservations.length" small>
        <v-icon>mdi-table</v-icon>Get CSV
      </v-btn>
    </v-card-actions>
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
      default: 5
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
      fields: [
        {
          text: 'Unit',
          value: 'unit_id',
          sortable: true
        },
        {
          text: 'Sequence',
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
          text: 'Date [UTC]',
          value: 'time',
          sortable: true
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
        }
        // { text: 'Image Count', value: 'image_count', sortable: true, type: 'number' },
      ]
    }
  },
  computed: {
    observations() {
      return this.$store.state.model.observations
    },
    lightcurves() {
      return this.$store.state.model.lightcurves
    },
    isSearching() {
      return this.$store.state.search.isSearching.observations
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
