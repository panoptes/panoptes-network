<template>
  <v-card v-if="observation">
    <v-card-text>
      <v-list dense>
        <v-list-item two-line>
          <v-list-item-content>
            <v-list-item-subtitle>Observation ID</v-list-item-subtitle>
            <v-list-item-title class="subtitle-2">
              <span>{{ observation.sequence_id }}</span>
            </v-list-item-title>
          </v-list-item-content>
        </v-list-item>
        <v-list-item two-line>
          <v-list-item-content>
            <v-list-item-subtitle>Observation Date</v-list-item-subtitle>
            <v-list-item-title class="subtitle-1">
              <span>{{ observation.time | moment('utc', 'YYYY-MM-DD HH:MM') }}</span>
              <strong>UTC</strong>
            </v-list-item-title>
          </v-list-item-content>
        </v-list-item>
        <v-list-item two-line>
          <v-list-item-content>
            <v-list-item-subtitle>RA / Dec</v-list-item-subtitle>
            <v-list-item-title class="subtitle-1">
              {{ observation.ra }}&deg;
              {{ observation.dec }}&deg;
            </v-list-item-title>
          </v-list-item-content>
        </v-list-item>
        <v-list-item two-line>
          <v-list-item-content>
            <v-list-item-subtitle>Exptime</v-list-item-subtitle>
            <v-list-item-title class="subtitle-1">{{ observation.exptime }} sec</v-list-item-title>
          </v-list-item-content>
        </v-list-item>

        <v-list-item two-line>
          <v-list-item-content>
            <v-list-item-subtitle>Status</v-list-item-subtitle>
            <v-list-item-title class="subtitle-1">{{ observation.status }}</v-list-item-title>
          </v-list-item-content>
        </v-list-item>

        <v-list-item two-line>
          <v-list-item-content>
            <v-list-item-subtitle>Field Name</v-list-item-subtitle>
            <v-list-item-title class="subtitle-1">{{ observation.field_name }}</v-list-item-title>
          </v-list-item-content>
        </v-list-item>

        <v-list-item two-line>
          <v-list-item-content>
            <v-list-item-subtitle>Unit ID</v-list-item-subtitle>
            <v-list-item-title class="subtitle-1">
              <nuxt-link :to="'/units/' + observation.unit_id">{{ observation.unit_id }}</nuxt-link>
            </v-list-item-title>
          </v-list-item-content>
        </v-list-item>

        <v-list-item two-line>
          <v-list-item-content>
            <v-list-item-subtitle>Camera ID</v-list-item-subtitle>
            <v-list-item-title class="subtitle-1">{{ observation.camera_id }}</v-list-item-title>
          </v-list-item-content>
        </v-list-item>

        <v-list-item two-line>
          <v-list-item-content>
            <v-list-item-subtitle>ISO</v-list-item-subtitle>
            <v-list-item-title class="subtitle-1">{{ observation.iso }}</v-list-item-title>
          </v-list-item-content>
        </v-list-item>

        <v-list-item two-line>
          <v-list-item-content>
            <v-list-item-subtitle>Software</v-list-item-subtitle>
            <v-list-item-title class="subtitle-1">{{ observation.software_version }}</v-list-item-title>
          </v-list-item-content>
        </v-list-item>
      </v-list>
    </v-card-text>
  </v-card>
</template>

<script>
export default {
  name: 'ObservationInfo',
  computed: {
    observation: function() {
      return this.$store.state.observations.selectedObservation
    },
    exptime: function() {
      return this.$store.state.observations.observation.exptime
    },
    num_images: function() {
      return this.$store.state.observations.images.length
    }
  },
  data() {
    return {}
  }
}
</script>

<style scoped>
.v-list-item__subtitle {
  text-transform: uppercase;
}
</style>
