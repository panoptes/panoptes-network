<template>
  <div class="sources">
	<section class="section">
	  <div class="container">
	    <Sources />
	  </div>
	</section>
  </div>
</template>

<script>
// @ is an alias to /src
import Sources from '@/components/Sources'

export default {
  name: 'sources',
  components: {
    Sources
  }
}
</script>
