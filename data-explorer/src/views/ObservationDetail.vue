<template>
  <div class="observations">
	  <div class="container">
			<ObservationDetail />
	  </div>
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
