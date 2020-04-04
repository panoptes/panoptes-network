<template>
  <v-card>
    <code>
      {{ observation }}
    </code>
  </v-card>
</template>
<script>

export default {
  name: 'LinkList',
  components: {},
  computed: {
    observation: function() {
      return this.$store.state.observations.selectedObservation
    }
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
