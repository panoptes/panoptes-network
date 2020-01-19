<template>
  <section class="section">
	  <div class="container">
			<SourceDetail />
	  </div>
  </section>
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
