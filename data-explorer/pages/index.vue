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
            >Lightcurves ({{ sources.length }})
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
import { mapState } from 'vuex'

// @ is an alias to /src
import Observations from '@/components/Observations'
// import Sources from '@/components/Sources'

export default {
  name: 'Home',
  components: {
    Observations
    // Sources
  },
  data: () => ({
    openPanels: [0, 1]
  }),
  computed: {
    ...mapState(['observations', 'searchModel'])
  }
}
</script>
