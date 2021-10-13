<template>
  <section class="section">
    <div class="card">
      <header class="card-header">
        <p class="card-header-title">Recent images</p>
      </header>
      <div class="card-content">
        <b-table :data="images" striped hoverable narrowed>
          <b-table-column field="time" label="Date" v-slot="props">{{ props.row.time.toDate().toLocaleString() }}</b-table-column>
          <b-table-column field="sequence_id" label="Observation" v-slot="props">{{
              props.row.sequence_id
            }}
          </b-table-column>
          <b-table-column field="id" label="ID" v-slot="props">{{ props.row.id }}</b-table-column>
          <b-table-column field="coords" label="Coords" v-slot="props">{{ props.row.ra_image.toFixed(2) }}°
            {{ props.row.dec_image.toFixed(2) }}°
          </b-table-column>
          <b-table-column field="exptime" label="Exptime" v-slot="props">{{ props.row.exptime }}</b-table-column>
          <b-table-column field="public_url" label="URL" v-slot="props">
            <b-button tag="a" :href="props.row.public_url" type="is-link is-light is-small">.FITS</b-button>
          </b-table-column>
          <b-table-column field="status" label="Status" v-slot="props">
            <span class="tag is-success is-uppercase">{{ props.row.status }}</span>
          </b-table-column>
        </b-table>
      </div>
    </div>
  </section>
</template>

<script>
import {db} from "../db";

export default {
  name: 'RecentImages',
  data() {
    return {
      images: [],
    }
  },
  firestore: {
    images: db.collection('images').orderBy('time', 'desc').limit(10)
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
