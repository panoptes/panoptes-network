<template>
  <v-layout column justify-center align-center>
    <v-flex xs12 sm8 md6>
      <v-expansion-panels :value="openPanels" accordion flat multiple>
        <!-- Observations -->
        <v-expansion-panel>
          <v-expansion-panel-header
            >Observations ({{ observations.length }})
          </v-expansion-panel-header>
          <v-expansion-panel-content>
            <Observations :perPage="5" :dense="true" />
          </v-expansion-panel-content>
        </v-expansion-panel>

        <!-- Lightcurves -->
        <v-expansion-panel>
          <v-expansion-panel-header
            >Lightcurves ({{ lightcurves.length }})
          </v-expansion-panel-header>
          <v-expansion-panel-content>
            <div class="text-center">
              <v-sheet class="yellow lighten-4">Coming Soon!</v-sheet>
            </div>
          </v-expansion-panel-content>
        </v-expansion-panel>
      </v-expansion-panels>
    </v-flex>
  </v-layout>
</template>

<script>
// @ is an alias to /src
import Observations from '@/components/Observations'

export default {
  name: 'Home',
  components: {
    Observations
  },
  data: () => ({
    openPanels: [0, 1]
  }),
  computed: {
    observations() {
      return this.$store.state.model.observations
    },
    lightcurves() {
      return this.$store.state.model.lightcurves
    }
  },
  async fetch({ store, params }) {
    // Lookup the most recent on page load.
    await store.dispatch('model/GET_RECENT')
  }
}
</script>
