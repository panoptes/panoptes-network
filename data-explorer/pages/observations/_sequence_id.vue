<template>
  <v-layout>
    <v-flex class="text-center"> Observation {{ sequence_id }} </v-flex>
  </v-layout>
</template>
<script>
export default {
  name: 'ObservationDetail',
  props: {},
  data() {
    return {
      sequence_id: this.$route.params.sequence_id
    }
  },
  computed: {}
}
</script>
