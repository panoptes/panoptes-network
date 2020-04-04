<template>
  <v-card outlined class="mx-auto" v-resize="onResize">
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
      :hide-default-headers="isMobile"
      :class="{mobile: isMobile}"
    >
      <template slot="item" slot-scope="props">
        <tr v-if="!isMobile">
          <td class="text-xs-right">
            <nuxt-link :to="'/unit/' + props.item.unit_id">{{props.item.unit_id }}</nuxt-link>
          </td>
          <td class="text-xs-right">
            <nuxt-link :to="'/observation/' + props.item.sequence_id">{{props.item.sequence_id }}</nuxt-link>
          </td>
          <td class="text-xs-right">{{ props.item.field_name }}</td>
          <td class="text-xs-right">{{ props.item.ra }}</td>
          <td class="text-xs-right">{{ props.item.dec }}</td>
          <td class="text-xs-right">{{ props.item.exptime }}</td>
          <td class="text-xs-right">{{ props.item.time | moment('utc', 'YYYY-MM-DD HH:mm')}}</td>
        </tr>
        <tr v-else>
          <td>
            <ObservationSummary :observation="props.item" />
          </td>
        </tr>
      </template>
    </v-data-table>
    <!--     <v-card-actions align="right">
      <v-spacer />
      <v-btn :disabled="state.search.hasResults" small>
        <v-icon>mdi-table</v-icon>Get CSV
      </v-btn>
    </v-card-actions>-->
  </v-card>
</template>
<script>
import ObservationSummary from '@/components/Observation/Summary'

export default {
  name: 'Observations',
  components: {
    ObservationSummary
  },
  filters: {
    formatUnitId: value => {
      /* This will format the unit_id with PAN and pre-pended zeros */
      // Silly formatting
      let unitId = 'PAN000'
      const l = -1 * value.toFixed(0).length
      unitId = unitId.slice(0, l)
      unitId += value
      return unitId
    },
    roundVal: value => {
      return parseFloat(value).toFixed(3)
    }
  },
  computed: {
    observations() {
      return this.$store.state.observations.observations
    },
    isSearching() {
      return this.$store.state.observations.isSearching
    }
  },
  methods: {
    onResize() {
      if (window.innerWidth < 769) this.isMobile = true
      else this.isMobile = false
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
      isMobile: false,
      fields: [
        {
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
