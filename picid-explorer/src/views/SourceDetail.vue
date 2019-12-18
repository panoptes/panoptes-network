<template>
  <div class="sources">
	  <div class="container">
			<SourceDetail />
	  </div>
  </div>
</template>

<script>
// @ is an alias to /src
import SourceDetail from '@/components/SourceDetail'

export default {
  name: 'sourceDetail',
  components: {
    SourceDetail
  },
  data () {
  	return {
  		picid: this.$route.params.picid
  	}
  }
}
</script>
