<template>
  <v-row>
    <v-col>
      <a :href="image_url" target="_blank">
        <v-btn x-small class="float-right">
          <v-icon small>mdi-open-in-new</v-icon>
        </v-btn>
      </a>
      <v-dialog v-model="dialog" v-if="selected">
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
        </v-img>
      </v-card>
    </v-col>
  </v-row>
</template>
<script>
export default {
  name: 'ImageViewer',
  computed: {
    image_url: function() {
      return this.selected.bucket_path.replace('processed', 'raw').replace('.fits.fz', '.jpg')
    },
    selected: function() {
      return this.$store.state.observation.selectedImage[0] || null
    }
  },
  data() {
    return {
      dialog: false
    }
  }
}

</script>
