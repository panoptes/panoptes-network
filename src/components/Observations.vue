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
      :dense="dense"
      :headers="fields"
      :items="observations"
      :items-per-page="perPage"
      :search="search"
      :loading="isSearching"
      class="elevation-1"
    >
    <template v-slot:item.unit_id="{ item }">
      <!-- <router-link :to="{ name: 'unitDetail', params: { unitId: item.unit_id }}"> -->
        {{ item.unit_id  }}
      <!-- </router-link> -->
    </template>
    <template v-slot:item.sequence_id="{ item }">
      <router-link
        :to="{ name: 'observationDetail', params: { sequenceId: item.sequence_id }}">
        {{ item.sequence_id }}
      </router-link>
    </template>
    <template v-slot:item.time="{ item }">
        {{ item.time | moment('YYYY-MM-DD HH:mm:ss ZZ') }}
    </template>
    </v-data-table>
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
    }
  },
  computed: {
    ...mapState([
      'units',
      'fromSearch',
      'sourceRows',
      'searchModel',
      'observations',
      'isSearching'
    ])
  },
  mounted: function () {
    this.$nextTick(function () {
      this.$store.dispatch('getRecent');
    })
  },
  props: [
    'perPage',
    'dense'
  ],
  data () {
    return {
      search: '',
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
          text: 'Date',
          value: 'time',
          sortable: true,
        },
        {
          text: 'Exp Time',
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
</style>
