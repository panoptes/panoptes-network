<template>
  <v-container>
    <v-row>
      <v-col>
        <!-- Observations -->
        <v-card>
          <v-card-title>Observations ({{ observations.length }})</v-card-title>
          <v-card-text>
            <Observations :per-page="10" :dense="true" />
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
    <v-row>
      <v-col>
        <!-- Lightcurves -->
        <v-card>
          <v-card-title>Lightcurves</v-card-title>
          <v-card-text>
            <div class="text-center">
              <v-sheet class="yellow lighten-4">Coming Soon!</v-sheet>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
// @ is an alias to /src
import Observations from '@/components/Observations'

export default {
  name: 'Home',
  components: {
    Observations
  },
  data: () => ({}),
  computed: {
    observations() {
      return this.$store.state.observations.observations
    }
  },
  async fetch({ store }) {
    // Lookup the most recent on page load.
    await store.dispatch('observations/GET_RECENT')
  }
}
</script>
