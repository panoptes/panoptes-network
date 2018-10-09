<template>
  <div class="observations">
	<section class="section">
	  <div class="container">
	    <Observations />
	  </div>
	</section>    
  </div>
</template>

<script>
// @ is an alias to /src
import Observations from '@/components/Observations'

export default {
  name: 'observations',
  components: {
    Observations
  }
}
</script>
