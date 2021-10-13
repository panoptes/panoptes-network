<template>
  <section class="section">
    <div class="card">
      <header class="card-header">
        <p class="card-header-title">Recent observations</p>
      </header>
      <div class="card-content has-text-left">
        <b-table :data="observations"
                 striped
                 hoverable
                 narrowed
                 paginated
                 per-page="5"
                 sort-icon="arrow-up"
                 detailed
                 detail-key="id"
        >
          <b-table-column field="time" label="Date" sortable v-slot="props">
            {{ props.row.time.toDate().toLocaleString() }}
          </b-table-column>
          <b-table-column field="id" label="ID" sortable v-slot="props">{{ props.row.id }}</b-table-column>
          <b-table-column field="field_name" label="Field name" sortable v-slot="props">{{ props.row.field_name }}</b-table-column>
          <b-table-column field="coords" label="Coords" sortable v-slot="props">
            <span v-if="props.row.ra">
              {{ props.row.ra.toFixed(2) }}° {{ props.row.dec.toFixed(2) }}°
            </span>
          </b-table-column>
          <b-table-column field="num_images" label="Images" sortable v-slot="props">{{ props.row.num_images }}</b-table-column>
          <b-table-column field="total_minutes_exptime" label="Total minutes" sortable v-slot="props">
            {{ props.row.total_minutes_exptime }}
          </b-table-column>
          <b-table-column field="status" label="Status" sortable v-slot="props">
            <b-tag type="is-success is-uppercase">{{ props.row.status }}</b-tag>
          </b-table-column>
          <template #detail="props">
            <pre>
            {{ props.row }}
            </pre>
          </template>
        </b-table>
      </div>
    </div>
  </section>
</template>

<script>
import {db} from "../db";

export default {
  name: 'Observations',
  data() {
    return {
      observations: [],
    }
  },
  firestore: {
    observations: db.collection('observations').orderBy('time', 'desc').limit(25)
  },
  methods: {}
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
h3 {
  margin: 40px 0 0;
}

ul {
  list-style-type: none;
  padding: 0;
}

li {
  display: inline-block;
  margin: 0 10px;
}

a {
  color: #42b983;
}
</style>
