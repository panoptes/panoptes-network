<template>
    <v-container>
        <v-row>
            <v-col>
                <Observations :perPage="5" :dense="true" />
            </v-col>
        </v-row>
        <v-row>
            <v-col>
                <Sources :perPage="5" :dense="true" />
            </v-col>
        </v-row>
    </v-container>
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
      'fromSearch',
      'searchModel',
      'observations',
      'isSearching'
    ])
  },
  components: {
    Observations,
    Sources
  }
}
</script>
