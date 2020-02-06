<template>
  <v-card>
    <v-data-table :headers="headers" :items="images" :items-per-page="5" class="elevation-1"></v-data-table>
    {{ images[0] }}
  </v-card>
</template>

<script>

export default {
  name: 'ImageLists',
  components: {
  },
  computed: {
    images: function() {
      return this.$store.state.observation.images
    }
  },
  data() {
    return {
      headers: [
        { text: 'RA', value: 'ra_image' },
        { text: 'Dec', value: 'dec_image' }
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