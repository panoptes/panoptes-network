<template>
  <v-expansion-panels
    accordion
    flat
    multiple
    :value="openPanels"
  >
    <!-- Observations -->
    <v-expansion-panel>
      <v-expansion-panel-header>
        Observations ({{ observations.length }})
      </v-expansion-panel-header>
      <v-expansion-panel-content>
        <Observations :perPage="5" :dense="true" />
      </v-expansion-panel-content>
    </v-expansion-panel>

        <!-- Observations -->
    <v-expansion-panel>
      <v-expansion-panel-header>
        Sources ({{ sources.length }})
      </v-expansion-panel-header>
      <v-expansion-panel-content>
        <Sources :perPage="5" :dense="true" />
      </v-expansion-panel-content>
    </v-expansion-panel>

  </v-expansion-panels>
</template>

<script>
import { mapState, mapActions } from 'vuex'

// @ is an alias to /src
import Observations from '@/components/Observations'
import Sources from '@/components/Sources'

export default {
  name: 'home',
  computed: {
    ...mapState([
      'units',
      'sources',
      'observations',
      'fromSearch',
      'searchModel',
    ]),
  },
  components: {
    Observations,
    Sources
  },
  data: () => ({
    openPanels: [0, 1]
  }),
}
</script>
