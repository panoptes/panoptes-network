<template>
    <v-card>
      <v-card-text>
        <v-row>
            <v-col cols="12">
                <v-list-item two-line>
                  <v-list-item-content>
                    <v-list-item-title class="caption text-uppercase">Observation ID</v-list-item-title>
                    <v-list-item-subtitle>
                      <span class="subtitle-1 font-weight-black">
                      {{ observation.sequence_id }}
                      </span>
                    </v-list-item-subtitle>
                  </v-list-item-content>
                </v-list-item>
              </v-col>
            </v-row>
        <v-row>
            <v-col cols="8">
                <v-list-item two-line>
                    <v-list-item-content>
                        <v-list-item-title class="caption text-uppercase">Observation Date</v-list-item-title>
                        <v-list-item-subtitle>
                          <span class="subtitle-1 font-weight-black">{{ observation.time | moment('utc', 'YYYY-MM-DD HH:MM') }}</span>
                          <strong>UTC</strong>
                        </v-list-item-subtitle>
                    </v-list-item-content>
                </v-list-item>
            </v-col>
            <v-col cols="4">
                <v-list-item two-line>
                    <v-list-item-content>
                        <v-list-item-title class="caption text-uppercase">Exptime</v-list-item-title>
                        <v-list-item-subtitle>
                          <span class="subtitle-1 font-weight-black" v-text="exptime"></span>
                          <strong>sec</strong>
                        </v-list-item-subtitle>
                    </v-list-item-content>
                </v-list-item>
            </v-col>
        </v-row>
        <v-row v-if="observation.ra">
            <v-col cols="8">
                <v-list-item two-line>
                    <v-list-item-content>
                        <v-list-item-title class="caption text-uppercase">RA / Dec</v-list-item-title>
                        <v-list-item-subtitle>
                          <span class="subtitle-1 font-weight-black" v-text="observation.ra"></span>
                          <span class="subtitle-1 font-weight-black">&deg;</span>
                          <span class="subtitle-1 font-weight-black" v-text="observation.dec"></span>
                          <span class="subtitle-1 font-weight-black">&deg;</span>
                        </v-list-item-subtitle>
                    </v-list-item-content>
                </v-list-item>
            </v-col>
        </v-row>
        <v-row v-else>
          <v-col class="display-3" cols="12">Unsolved</v-col>
        </v-row>
      <v-divider></v-divider>
      <v-list
        class="infolist"
        dense>
        <v-list-item>
          <v-list-item-subtitle>Status</v-list-item-subtitle>
          <v-list-item-title class="text-left">{{ observation.status }}</v-list-item-title>
        </v-list-item>

        <v-list-item>
          <v-list-item-subtitle>Field Name</v-list-item-subtitle>
          <v-list-item-title class="text-left">{{ observation.field_name }}</v-list-item-title>
        </v-list-item>

        <v-list-item>
          <v-list-item-subtitle>Unit ID</v-list-item-subtitle>
          <v-list-item-title class="text-left">
            <nuxt-link :to="'/units/' + observation.unit_id">
              {{ observation.unit_id }}
            </nuxt-link>
            </v-list-item-title>
        </v-list-item>

        <v-list-item>
          <v-list-item-subtitle>Camera ID</v-list-item-subtitle>
          <v-list-item-title class="text-left">{{ observation.camera_id }}</v-list-item-title>
        </v-list-item>

        <v-list-item>
          <v-list-item-subtitle>ISO</v-list-item-subtitle>
          <v-list-item-title class="text-left">{{ observation.iso }}</v-list-item-title>
        </v-list-item>

        <v-list-item>
          <v-list-item-subtitle>Software</v-list-item-subtitle>
          <v-list-item-title class="text-left">
            {{ observation.software_version }}
          </v-list-item-title>
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
      return this.$store.state.observation.observation
    },
    exptime: function() {
        return this.$store.state.observation.observation.exptime
    },
    num_images: function() {
      return this.$store.state.observation.images.length
    }
  },
  data() {
    return {}
  }
}
</script>

