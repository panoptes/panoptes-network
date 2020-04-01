<template>
  <v-card height="100%">
    <v-card-title>Image List <v-spacer></v-spacer> <span class="overline">(Total: {{ images.length }})</span></v-card-title>
    <v-data-table
      :headers="headers"
      :items="images"
      :items-per-page="20"
      :dense=true
      sort-by="time"
      class="elevation-1"
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
        <a :href="'https://storage.googleapis.com/panoptes-raw-images/' + item.bucket_path">FITS</a>
        <v-icon small>mdi-open-in-new</v-icon>
      </template>
    </v-data-table>
  </v-card>
</template>

<script>
export default {
  name: 'ImageLists',
  components: {},
  computed: {
    images: function() {
      return this.$store.state.observation.images
    }
  },
  data() {
    return {
      headers: [
        // { text: 'ID', value: 'image_id' },
        { text: 'Time', value: 'time' },
        { text: 'HA', value: 'ha_mnt' },
        // { text: 'RA', value: 'ra_image' },
        // { text: 'Dec', value: 'dec_image' },
        { text: 'Airmass', value: 'airmass' },
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
