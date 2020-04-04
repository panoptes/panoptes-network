<template>
  <v-container fluid>
    <v-data-iterator
      v-if="units"
      :items="units"
      :items-per-page.sync="itemsPerPage"
      hide-default-footer
    >
      <template v-slot:default="props">
        <v-row>
          <v-col
            v-for="item in units"
            :key="item.unit_id"
            cols="12"
            sm="6"
            md="4"
            lg="3"
          >
          <nuxt-link :to="'/unit/' + item.unit_id">
            <UnitInfo :unit="item" />
          </nuxt-link>
          </v-col>
        </v-row>
      </template>
    </v-data-iterator>
  </v-container>
</template>

<script>
import UnitInfo from '@/components/Unit'


export default {
  name: 'Units',
  components: {
    UnitInfo
  },
  data: () => ({
    itemsPerPage: 4,
  }),
  computed: {
    units() {
      return this.$store.state.unit.units
    }
  },
  async fetch({ store }) {
    await store.dispatch('units/GET_UNITS')
  }
}

</script>
