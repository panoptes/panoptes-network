<template>
  <div>
    {{ sequence_id }}
    <br >
    <dl class="row">
      <dt class="col-sm-3">PANID</dt>
      <dd class="col-sm-9">{{ unit_id }}</dd>

      <dt class="col-sm-3">Start date</dt>
      <dd class="col-sm-9">{{ time | moment("YYYY-MM-DD HH:mm:ss") }}</dd>

      <dt class="col-sm-3">Exptime</dt>
      <dd class="col-sm-9">{{ exptime }}</dd>

      <dt class="col-sm-3">POCS Version</dt>
      <dd class="col-sm-9">{{ software_version }}</dd>
    </dl>
  </div>
</template>

<script>
export default {
  name: 'ObservationDetail',
  computed: {
    observation: {
      get () {
        return this.$store.state.observation.observation
      },
      set (obj) {
        this.$store.commit('observation/UPDATE_OBSERVATION', obj)
      }
    }
  }
}
</script>
