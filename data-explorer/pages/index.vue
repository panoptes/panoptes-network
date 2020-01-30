<template>
  <v-layout column justify-center align-center>
    <v-flex xs12 sm8 md6>
      <PanLogo />
      <v-card>
        <v-card-title class="headline">
          {{ title }}
        </v-card-title>
        <v-card-text>
          Hello.
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn color="primary" nuxt to="/observations">
            Continue
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-flex>
  </v-layout>
</template>

<script>
import PanLogo from '~/components/PanLogo.vue'

export default {
  components: {
    PanLogo
  }
}
</script>
