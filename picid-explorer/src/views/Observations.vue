<template>
  <div class="columns">
    <div class="column">
  	    <Observations />
    </div>
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
