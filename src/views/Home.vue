<template>
    <v-content>
        <Observations :perPage="5" :dense="true" />
        <v-divider></v-divider>
        <Sources :perPage="5" :dense="true" />
    </v-content>
</template>

<script>
// @ is an alias to /src
import Observations from '@/components/Observations'
import Sources from '@/components/Sources'

export default {
  name: 'home',
  components: {
    Observations,
    Sources
  }
}
</script>
