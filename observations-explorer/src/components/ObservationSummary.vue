<template>
<div>
  <dl class="row">
    <dt class="col-sm-3">PANID</dt>
    <dd class="col-sm-9">{{ sequence.unit_id | unitId }}</dd>

    <dt class="col-sm-3">Field</dt>
    <dd class="col-sm-9">{{ sequence.field }}</dd>

    <dt class="col-sm-3">Start date</dt>
    <dd class="col-sm-9">{{ sequence.start_date | moment("YYYY-MM-DD HH:mm:ss") }}</dd>

    <dt class="col-sm-3">Exptime</dt>
    <dd class="col-sm-9">{{ sequence.exp_time }}</dd>

    <dt class="col-sm-3">POCS Version</dt>
    <dd class="col-sm-9">{{ sequence.pocs_version }}</dd>    

    <dt class="col-sm-3">State</dt>
    <dd class="col-sm-9">{{ sequence.piaa_state }}</dd>        


    <dt class="col-sm-3">Images</dt>
    <dd class="col-sm-9">{{ sequence.image_count }}</dd>            
  </dl>
</div>
</template>

<script>
import { ObservationsService } from '../services/ObservationsService.js'

const baseUrl = 'https://storage.googleapis.com/panoptes-survey'

let observations = new ObservationsService()

export default {
  name: 'ObservationSummary',
  components: {
  },
  props: {
    sequence: Object
  },
  filters: {
    unitId: function (value) {
      // Silly formatting
      let unitId = 'PAN000'
      if (value !== undefined) {
        let l = -1 * value.toFixed(0).length
        unitId = unitId.slice(0, l)
        unitId += value
      } else {
        unitId = value
      }
      return unitId      
    }
  },  
  created () {
    // if (this.sequence === null) {
    //   this.observations.getObservation(this.sequenceId).then(response => {
    //     this.sequence = response.data.data
    //   })
    //     .catch(error => {
    //       console.log(error)
    //     })
    //     .finally(() => (this.loading = false))
    // }
  },
  data () {
    return {
      observations: observations
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
.info {

}
</style>
