<template>
  <v-card
    class="mx-auto"
    max-width="344"
    outlined
  >
    <v-list-item three-line>
      <v-list-item-content>
        <div class="overline mb-4">{{ unit.status }}</div>
        <v-list-item-title class="headline mb-1">{{ unit.unit_id }}</v-list-item-title>
        <v-list-item-subtitle>{{ unit.name }}</v-list-item-subtitle>
      </v-list-item-content>

    </v-list-item>

    <v-card-text>
    Observations: {{ unit.num_observations }} <br />
    Location: {{ unit.location._lat.toFixed(2) }}&deg; {{ unit.location._long.toFixed(2) }}&deg; <br />
    Elevation: {{ unit.elevation }} meters<br />
    </v-card-text>

  </v-card>
</template>

<script>
export default {
  name: 'UnitInfo',
  props: {
    unit: {
      type: Object,
      default: null
    }
  },
  data() {
    return {}
  }
}

</script>
