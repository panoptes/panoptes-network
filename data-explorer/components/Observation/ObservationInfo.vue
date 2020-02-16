<template>
    <v-card class="mx-auto" max-width="500">
      <v-list-item two-line>
        <v-list-item-content>
          <v-list-item-title class="headline">{{ observation.time }}</v-list-item-title>
          <v-list-item-subtitle>{{ observation.field_name }}</v-list-item-subtitle>
        </v-list-item-content>
      </v-list-item>

      <v-card-text>
        <v-row v-if="observation.ra">
            <v-col cols="6">
                <v-list-item two-line>
                    <v-list-item-content>
                        <v-list-item-title class="caption text-uppercase">RA</v-list-item-title>
                        <v-list-item-subtitle>
                          <span class="display-2 font-weight-black" v-text="observation.ra"></span>
                          <span class="display-2 font-weight-black">&deg;</span>
                        </v-list-item-subtitle>
                    </v-list-item-content>
                </v-list-item>
            </v-col>
            <v-col cols="6">
                <v-list-item two-line>
                    <v-list-item-content>
                        <v-list-item-title class="caption text-uppercase">Dec</v-list-item-title>
                        <v-list-item-subtitle>
                          <span class="display-2 font-weight-black" v-text="observation.dec"></span>
                          <span class="display-2 font-weight-black">&deg;</span>
                        </v-list-item-subtitle>
                    </v-list-item-content>
                </v-list-item>
            </v-col>
        </v-row>
        <v-row v-else>
          <v-col class="display-3" cols="12">Unsolved</v-col>
        </v-row>
        <v-divider></v-divider>
        <v-row>
            <v-col cols="6">
                <v-list-item two-line>
                    <v-list-item-content>
                        <v-list-item-title class="caption text-uppercase">Exptime</v-list-item-title>
                        <v-list-item-subtitle>
                        <span class="display-2" v-text="exptime"></span>
                        <strong>sec</strong>
                        </v-list-item-subtitle>
                    </v-list-item-content>
                </v-list-item>
            </v-col>
            <v-col cols="6">
                <v-list-item two-line>
                    <v-list-item-content>
                        <v-list-item-title class="caption text-uppercase">Images</v-list-item-title>
                        <v-list-item-subtitle>
                        <span class="display-2" v-text="observation.num_images"></span>
                        </v-list-item-subtitle>
                    </v-list-item-content>
                </v-list-item>
            </v-col>
        </v-row>
      </v-card-text>

      <v-divider></v-divider>
      <v-list class="transparent">
        <v-list-item>
          <v-list-item-title>Sequence ID</v-list-item-title>
          <v-list-item-subtitle class="text-left">{{ observation.sequence_id }}</v-list-item-subtitle>
        </v-list-item>

        <v-list-item>
          <v-list-item-title>Status</v-list-item-title>
          <v-list-item-subtitle class="text-left">{{ observation.status }}</v-list-item-subtitle>
        </v-list-item>

        <v-list-item>
          <v-list-item-title>Field Name</v-list-item-title>
          <v-list-item-subtitle class="text-left">{{ observation.field_name }}</v-list-item-subtitle>
        </v-list-item>

        <v-list-item>
          <v-list-item-title>Unit ID</v-list-item-title>
          <v-list-item-subtitle class="text-left">
            <nuxt-link :to="'/units/' + observation.unit_id">
              {{ observation.unit_id }}
            </nuxt-link>
            </v-list-item-subtitle>
        </v-list-item>

        <v-list-item>
          <v-list-item-title>Camera ID</v-list-item-title>
          <v-list-item-subtitle class="text-left">{{ observation.camera_id }}</v-list-item-subtitle>
        </v-list-item>

        <v-list-item>
          <v-list-item-title>ISO</v-list-item-title>
          <v-list-item-subtitle class="text-left">{{ observation.iso }}</v-list-item-subtitle>
        </v-list-item>

        <v-list-item>
          <v-list-item-title>Software</v-list-item-title>
          <v-list-item-subtitle class="text-left">
            {{ observation.software_version }}
            {{ observation.pocs_version }}
          </v-list-item-subtitle>
        </v-list-item>
      </v-list>
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
        return this.$store.state.observation.images[0].exptime
    }
  },
  data() {
    return {}
  }
}
</script>
