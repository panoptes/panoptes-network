<template>
  <v-row>
    <v-card class="mx-auto" max-width="500">
      <v-list-item two-line>
        <v-list-item-content>
          <v-list-item-title class="headline">{{ observation.time }}</v-list-item-title>
          <v-list-item-subtitle>{{ observation.field_name }}</v-list-item-subtitle>
        </v-list-item-content>
      </v-list-item>

      <v-card-text>
        <v-row v-if="observation.ra">
          <v-col class="display-3" cols="12">{{ observation.ra }}&deg; {{ observation.dec }}&deg;</v-col>
        </v-row>
        <v-row v-else>
          <v-col class="display-3" cols="12">Unsolved</v-col>
        </v-row>
      </v-card-text>

      <v-list class="transparent">
        <v-list-item>
          <v-list-item-title>Sequence ID</v-list-item-title>
          <v-list-item-subtitle class="text-left">{{ observation.sequence_id }}</v-list-item-subtitle>
        </v-list-item>

        <v-list-item>
          <v-list-item-title>Field Name</v-list-item-title>
          <v-list-item-subtitle class="text-left">{{ observation.field_name }}</v-list-item-subtitle>
        </v-list-item>

        <v-list-item>
          <v-list-item-title>Status</v-list-item-title>
          <v-list-item-subtitle class="text-left">{{ observation.status }}</v-list-item-subtitle>
        </v-list-item>

        <v-list-item>
          <v-list-item-title>Coordinates</v-list-item-title>
          <v-list-item-subtitle
            v-if="observation.ra"
            class="text-left"
          >{{ observation.ra }}&deg; {{ observation.dec }}&deg;</v-list-item-subtitle>
          <v-list-item-subtitle v-else class="text-left">Unsolved</v-list-item-subtitle>
        </v-list-item>

        <v-list-item>
          <v-list-item-title>Unit ID</v-list-item-title>
          <v-list-item-subtitle class="text-left">{{ observation.unit_id }}</v-list-item-subtitle>
        </v-list-item>

        <v-list-item>
          <v-list-item-title>Camera ID</v-list-item-title>
          <v-list-item-subtitle class="text-left">{{ observation.camera_id }}</v-list-item-subtitle>
        </v-list-item>

        <v-list-item>
          <v-list-item-title>Exptime</v-list-item-title>
          <v-list-item-subtitle class="text-left">{{ observation.exptime }} sec.</v-list-item-subtitle>
        </v-list-item>

        <v-list-item>
          <v-list-item-title>ISO</v-list-item-title>
          <v-list-item-subtitle class="text-left">{{ observation.iso }}</v-list-item-subtitle>
        </v-list-item>

        <v-list-item>
          <v-list-item-title>Num Images</v-list-item-title>
          <v-list-item-subtitle class="text-left">{{ observation.num_images }}</v-list-item-subtitle>
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

    <AirmassCard />
    <ImageList />
  </v-row>
</template>

<script>
import ImageList from '@/components/Observation/ImageList'
import AirmassCard from '@/components/Observation/AirmassCard'

export default {
  name: 'ObservationDetail',
  components: { AirmassCard, ImageList },
  computed: {
    observation: {
      get() {
        return this.$store.state.observation.observation
      }
    }
  },
  data() {
    return {}
  }
}
</script>
