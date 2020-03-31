<template>
  <v-container>
  <v-card class="mx-auto statCard" color="grey lighten-4">
    <v-list-item two-line>
      <v-list-item-content>
        <v-list-item-title class="caption text-uppercase">{{ name }}</v-list-item-title>
        <v-list-item-subtitle>
          <span class="display-2" v-text="avg || '—'"></span>
          <strong v-if="avg">{{ units }}</strong>
        </v-list-item-subtitle>
      </v-list-item-content>
    </v-list-item>

    <v-sheet v-if="showSparkline" color="transparent">
      <v-sparkline
        :key="String(avg)"
        :smooth="16"
        :gradient="['#000000', '#0f0df0']"
        :line-width="3"
        :value="values"
        auto-draw
        stroke-linecap="round"
      ></v-sparkline>
    </v-sheet>
  </v-card>
  </v-container>
</template>

<script>
export default {
  computed: {
    avg() {
      if (this.values.length > 0) {
        const sum = this.values.reduce((acc, cur) => acc + cur, 0)
        const length = this.values.length

        if (!sum && !length) return 0

        return (sum / length).toFixed(2)
      } else {
        return this.values
      }
    }
  },
  props: {
    name: {
      type: String,
      default: '',
      required: true
    },
    units: {
      type: String,
      default: '',
      required: false
    },
    values: {
      type: [Array, Number],
      required: true
    },
    showSparkline: {
      type: Boolean,
      default: false,
      required: false
    }
  },
  data() {
    return {}
  }
}
</script>

<style>
.v-sheet--offset {
  top: -24px;
  position: relative;
}
.caption {
  margin: 2px;
}
.statCard {
  min-width: 12rem;
  min-height: 12rem;
  max-width: 12rem;
  max-height: 12rem;
}
</style>
