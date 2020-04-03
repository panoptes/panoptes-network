<template>
  <v-card>

  </v-card>
</template>
<script>
import { mapMutations } from 'vuex'

export default {
  name: 'LinkList',
  components: {},
  computed: {
    images: function() {
      return this.$store.state.observation.images
    },
    image_url: function() {
      return this.selected[0].bucket_path.replace('processed', 'raw').replace('.fits.fz', '.jpg')
    },
  },
  mounted: function() {
    this.$nextTick(function() {
    })
  },
  data() {
    return {
    }
  }
}

</script>
<style>

</style>
