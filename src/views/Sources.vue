<template>
  <div class="columns">
  	<div class="column">
  	    <Sources />
  	</div>
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
