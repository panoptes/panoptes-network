<template>
 <v-card>
    <v-card-title>
      <v-text-field
        v-model="search"
        append-icon="mdi-magnify"
        label="Filter Sources"
        single-line
        hide-details
      ></v-text-field>
    </v-card-title>
    <v-data-table
      :dense="dense"
      :headers="fields"
      :items="sourceRows"
      :items-per-page="perPage"
      :search="search"
      :loading="isSearching"
      class="elevation-1"
    >
      <template v-slot:item.id="{ item }">
        <template slot="header" slot-scope="{ column }">
          <b-tooltip label="PANOPTES Input Catalog ID" dashed>
          {{ column.label }}
          </b-tooltip>
        </template>
        <router-link
          :to="{ name: 'sourceDetail', params: { picid: item.id }}">
        {{ item.id }}
        </router-link>
      </template>
      <template v-slot:item.ra="{ item }">
        {{ item.ra.toFixed(3) }}
      </template>
      <template v-slot:item.dec="{ item }">
        {{ item.dec.toFixed(3) }}
      </template>
      <template v-if="fromSearch" v-slot:item.distance="{ item }">
        {{ item.distance.toFixed(3) }}
      </template>
      <template v-slot:item.lumclass="{ item }">
        {{ item.lumclass }}
      </template>
      <template v-slot:item.vmag="{ item }">
        {{ item.vmag.toFixed(2) }}
      </template>
      <template v-slot:item.picid="{ item }">
        <a v-bind:href="'https://exofop.ipac.caltech.edu/tess/target.php?id=' + item.id" target="_blank">
          ExoFOP
        </a>
      </template>
    </v-data-table>
  </v-card>
</template>

<script>
import { mapState, mapActions } from 'vuex'

export default {
  name: 'Sources',
  computed: {
    ...mapState([
      'fromSearch',
      'sourceRows',
      'searchModel',
      'isSearching'
    ]),
  },
  methods: {
    submitForm: function() {
      this.$store.dispatch('setSource', this.gotoPicid);
      this.$router.push({ name: 'sourceDetail', params: { picid: this.gotoPicid }});
    }
  },
  created () {
    // Look up the most recent sources.
    this.$store.dispatch('getRecentSources');
  },
  props: [
    'perPage',
    'dense'
  ],
  data () {
    return {
      currentPage: 1,
      loading: false,
      gotoPicid: null,
      search: '',
      fields: [
        {
          text: 'PICID',
          value: 'id',
          sortable: true
        },
        {
          text: 'RA',
          value: 'ra',
          sortable: true
        },
        {
          text: 'Dec',
          value: 'dec',
          sortable: true
        },
        {
          text: 'Distance',
          value: 'distance',
          sortable: true,
          align: ' d-none'
        },
        {
          text: 'Class',
          value: 'lumclass',
          sortable: true
        },
        {
          text: 'Vmag',
          value: 'vmag',
          sortable: true
        },
        {
          text: '',
          value: 'picid',
          sortable: true
        }
      ]
    }
  }
}
</script>

