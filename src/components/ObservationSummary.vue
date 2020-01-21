<template>
<div>
  <dl class="row">
    <dt class="col-sm-3">PANID</dt>
    <dd class="col-sm-9">{{ sequence.unit_id }}</dd>

    <dt class="col-sm-3">Field</dt>
    <dd class="col-sm-9">{{ sequence.field }}</dd>

    <dt class="col-sm-3">Start date</dt>
    <dd class="col-sm-9">{{ sequence.start_date | moment("YYYY-MM-DD HH:mm:ss") }}</dd>

    <dt class="col-sm-3">Exptime</dt>
    <dd class="col-sm-9">{{ sequence.exptime }}</dd>

    <dt class="col-sm-3">POCS Version</dt>
    <dd class="col-sm-9">{{ sequence.pocs_version }}</dd>

    <dt class="col-sm-3">Images</dt>
    <dd class="col-sm-9">{{ sequence.image_count }}</dd>

    <dt class="col-sm-3">Bucket Path</dt>
    <dd class="col-sm-9">{{ sequenceDir }}</dd>
  </dl>
</div>
</template>

<script>
import { mapState, mapActions } from 'vuex'

const baseUrl = 'https://storage.googleapis.com/panoptes-survey'

export default {
  name: 'ObservationSummary',
  props: {
    sequence: Object,
    sequenceDir: ''
  },
  computed: {
    ...mapState([
      'units',
      'fromSearch',
      'sourceRows',
      'searchModel',
      'observations',
      'isSearching'
    ])
  },
  data () {
    return {
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
.info {

}
</style>
