<template>
  <v-card outlined>
    <v-card-title>
      <v-text-field
        v-model="search"
        append-icon="mdi-magnify"
        label="Filter Sources"
        single-line
        hide-details
      />
    </v-card-title>
    <v-data-table
      :dense="dense"
      :headers="fields"
      :items="sources"
      :items-per-page="perPage"
      :search="search"
      :loading="isSearching"
      class="elevation-1"
    >
      <template v-slot:body="{ items }">
        <tbody>
          <tr v-for="item in items" :key="item.picid">
            <td>
              <template slot="header" slot-scope="{ column }">
                <b-tooltip label="PANOPTES Input Catalog ID" dashed>
                  {{ item.picid }}
                </b-tooltip>
              </template>
              <router-link
                :to="{ name: 'sourceDetail', params: { picid: item.picid } }"
              >
                {{ item.picid }}
              </router-link>
            </td>
            <td>
              {{ item.ra }}
            </td>
            <td>
              {{ item.dec }}
            </td>
            <td v-if="fromSearch">
              {{ item.distance }}
            </td>
            <td>
              {{ item.lumclass | removeNan }}
            </td>
            <td>
              {{ item.vmag.toFixed(2) }}
            </td>
            <td>
              <a
                :href="
                  'https://exofop.ipac.caltech.edu/tess/target.php?id=' +
                    item.picid
                "
                target="_blank"
              >
                ExoFOP
              </a>
            </td>
          </tr>
        </tbody>
      </template>
    </v-data-table>

    <v-card-actions v-if="allowDownloads" align="right">
      <v-spacer />
      <v-btn small :disabled="!selectedStars.length">
        <v-icon>mdi-table</v-icon> Get CSV
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script>
import { mapState, mapActions } from 'vuex'

export default {
  name: 'Sources',
  computed: {
    ...mapState(['searchModel', 'fromSearch', 'sources']),
    isSearching: function() {
      return this.searchModel.isSearching['stars']
    }
  },
  methods: {
    submitForm: function() {
      this.$store.dispatch('setSource', this.gotoPicid)
      this.$router.push({
        name: 'sourceDetail',
        params: { picid: this.gotoPicid }
      })
    }
  },
  filters: {
    removeNan: function(val) {
      if (typeof val === 'number') {
        val = ''
      }
      return val
    }
  },
  props: ['perPage', 'dense'],
  data() {
    return {
      currentPage: 1,
      loading: false,
      gotoPicid: null,
      selectedStars: [],
      allowDownloads: false,
      search: '',
      fields: [
        {
          text: 'PICID',
          value: 'picid',
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
          text: 'Links',
          value: 'picid',
          sortable: true
        }
      ]
    }
  }
}
</script>
