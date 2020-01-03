<template>
  <div class="columns">
	<column class="column">
	    <Sources />
	</column>
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
