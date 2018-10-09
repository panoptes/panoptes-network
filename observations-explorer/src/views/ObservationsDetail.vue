<template>
  <div class="observations">
  	<h2> {{ sequenceId }} </h2>
  	<ObservationDetail />
  </div>
</template>

<script>
// @ is an alias to /src
import ObservationDetail from '@/components/ObservationDetail'

export default {
  name: 'observationDetail',
  components: {
    ObservationDetail
  },
  data () {
  	return {
  		sequenceId: this.$route.params.sequenceId
  	}
  } 
}
</script>
