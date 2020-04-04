<template>
  <v-container>
    <v-row v-if="selected.length">
      <v-col>
        <a :href="image_url" target="_blank">
          <v-btn x-small class="float-right">
            <v-icon small>mdi-open-in-new</v-icon>
          </v-btn>
        </a>
        <v-dialog v-model="dialog">
          <template v-slot:activator="{ on }">
            <v-img :src="image_url" v-on="on"></v-img>
          </template>
          <v-card>
            <v-img :src="image_url"></v-img>
          </v-card>
        </v-dialog>
        <v-card height="100%" flat>
          <template v-slot:placeholder>
            <v-row class="fill-height ma-0" align="center" justify="center">
              <v-progress-circular indeterminate color="purple"></v-progress-circular>
            </v-row>
          </template>
        </v-card>
      </v-col>
    </v-row>
    <v-row>
      <v-col>
        <v-card height="100%">
          <v-card-title>
            Image List
            <v-spacer></v-spacer>
            <span class="overline">(Total: {{ images.length }})</span>
          </v-card-title>
          <v-data-table
            v-model="selected"
            :headers="headers"
            :items="images"
            :items-per-page="20"
            :dense="true"
            :show-select="false"
            :single-select="singleSelect"
            item-key="image_id"
            @click:row="setRow"
            sort-by="time"
            class="elevation-1"
            :show-expand="false"
            :expanded.sync="expanded"
          >
            <template v-slot:item.image_id="{ item }">
              <nuxt-link :to="'/images/' + item.image_id">
                {{
                item.image_id
                }}
              </nuxt-link>
            </template>
            <template v-slot:item.ha_mnt="{ item }">{{ item.ha_mnt.toFixed(3) }}</template>
            <template v-slot:item.time="{ item }">{{ item.time | moment('utc', 'HH:mm:ss') }}</template>
            <template v-slot:item.ra_image="{ item }">{{ item.ra_image.toFixed(3) }}</template>
            <template v-slot:item.dec_image="{ item }">{{ item.dec_image.toFixed(3) }}</template>
            <template v-slot:item.airmass="{ item }">{{ item.airmass.toFixed(3) }}</template>
            <template v-slot:item.moonsep="{ item }">{{ item.moonsep.toFixed(2) }}</template>
            <template v-slot:item.moonsep="{ item }">{{ item.moonsep.toFixed(2) }}</template>
            <template v-slot:item.moonfrac="{ item }">{{ item.moonfrac.toFixed(2) }}</template>
            <template v-slot:item.status="{ item }">{{ item.status }}</template>
            <template v-slot:item.bucket_path="{ item }">
              <a
                :href="'https://storage.googleapis.com/panoptes-raw-images/' + item.bucket_path"
              >FITS</a>
              <v-icon small>mdi-open-in-new</v-icon>
            </template>
            <template v-slot:expanded-item="{ headers, item }">
              <td :colspan="headers.length">
                <code>{{ item }}</code>
              </td>
            </template>
          </v-data-table>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>
<script>
import { mapMutations } from 'vuex'

export default {
  name: 'ImageLists',
  components: {},
  computed: {
    images: function() {
      return this.$store.state.observations.images
    },
    image_url: function() {
      return this.selected[0].bucket_path
        .replace('processed', 'raw')
        .replace('.fits.fz', '.jpg')
    }
  },
  mounted: function() {
    this.$nextTick(function() {
      this.setRow(this.images[0])
    })
  },
  methods: {
    setRow(row) {
      this.selected = [row]
      this.$store.commit('observations/SET_IMAGE', row)
      this.dialog = false
    }
  },
  data() {
    return {
      dialog: true,
      singleSelect: true,
      selected: [],
      expanded: [],
      headers: [
        // { text: 'ID', value: 'image_id' },
        { text: 'Time', value: 'time' },
        { text: 'HA', value: 'ha_mnt' },
        // { text: 'RA', value: 'ra_image' },
        // { text: 'Dec', value: 'dec_image' },
        { text: 'Airmass', value: 'airmass' }
        // { text: 'Moon Sep', value: 'moonsep' },
        // { text: 'Moon Frac', value: 'moonfrac' },
        // { text: 'Status', value: 'status' },
        // { text: 'FITS', value: 'bucket_path' }
      ]
    }
  }
}
</script>
<style>
.v-sheet--offset {
  top: -24px;
  position: relative;
}
</style>
