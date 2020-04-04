<template>
  <v-card class="d-inline-block mx-auto" flat>
    <v-card-text>
      <div>
        <nuxt-link :to="'/observation/' + observation.sequence_id">{{observation.sequence_id }}</nuxt-link>
        <br />
        {{ observation.time | moment('utc', 'YYYY-MM-DD HH:mm') }}
        <br />
        <br />
        <nuxt-link :to="'/unit/' + observation.unit_id">{{observation.unit_id }}</nuxt-link>
        <br />
        Field: {{ observation.field_name }}
        <br />
        Coords: {{ observation.ra }}&deg;  {{ observation.dec }} &deg;
        <br />
        Exptime: {{ observation.exptime }} seconds
        <br />
        Images: {{ observation.num_images }}
      </div>
    </v-card-text>
  </v-card>
</template>

<script>
export default {
  name: 'ObservationSummary',
  computed: {},
  props: {
    observation: {
      type: Object,
      default: null,
      required: true
    }
  },
  data() {
    return {}
  }
}
</script>

<style scoped>
.mobile {
  color: #333;
}

@media screen and (max-width: 768px) {
  .v-card__text {
      padding-left: 0
  }
  .mobile table.v-table tr {
    max-width: 100%;
    position: relative;
    display: block;
  }

  .mobile table.v-table tr:nth-child(odd) {
    border-left: 6px solid deeppink;
  }

  .mobile table.v-table tr:nth-child(even) {
    border-left: 6px solid cyan;
  }

  .mobile table.v-table tr td {
    display: flex;
    width: 100%;
    border-bottom: 1px solid #f5f5f5;
    height: auto;
    padding: 10px;
  }

  .mobile table.v-table tr td ul li:before {
    content: attr(data-label);
    padding-right: 0.5em;
    text-align: left;
    display: block;
    color: #999;
  }
  .v-datatable__actions__select {
    width: 50%;
    margin: 0px;
    justify-content: flex-start;
  }
  .mobile .theme--light.v-table tbody tr:hover:not(.v-datatable__expand-row) {
    background: transparent;
  }
}

</style>
