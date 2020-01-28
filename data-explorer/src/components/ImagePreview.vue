<template>
<article class="media">
  <figure class="media-left" @click="isImageModalActive = true">
      <p class="image is-128x128">
        <img :src="image.file_path | toJpg">
      </p>
    <b-modal :active.sync="isImageModalActive">
      <figure class="image">
        <img :src="image.file_path | toJpg">
      </figure>
    </b-modal>      
  </figure>
  <div class="media-content">
    <div class="content">
        <strong> {{ image.obstime }} </strong>
      <ul>
        <li v-for="(value, key) in image">
          {{ key }}: {{ value }}
        </li>
      </ul>
    </div>
  </div>
</article>
</template>

<script>
export default {
  name: 'HelloWorld',
  props: {
    image: Object
  },
  filters: {
    toJpg: function (value) {
      return value.replace(".fits.fz", ".jpg")
    }
  },
  data () {
    return {
      isImageModalActive: false
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped lang="scss">
</style>
