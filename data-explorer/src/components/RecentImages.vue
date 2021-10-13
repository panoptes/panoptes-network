<template>
  <section class="section">
    <div class="card">
      <header class="card-header">
        <p class="card-header-title">Recent images</p>
      </header>
      <div class="card-content has-text-left">
        <b-table :data="images"
                 striped
                 hoverable
                 narrowed
                 paginated
                 per-page="5"
                 default-sort="time"
                 sort-icon="arrow-up">
          <b-table-column field="time" label="Date" sortable v-slot="props">
            {{ props.row.time.toDate().toLocaleString() }}
          </b-table-column>
          <b-table-column field="id" label="ID" sortable v-slot="props">{{ props.row.id }}</b-table-column>
          <b-table-column field="coords" label="Coords" sortable v-slot="props">
            {{ props.row.ra_image.toFixed(2) }}°
            {{ props.row.dec_image.toFixed(2) }}°
          </b-table-column>
          <b-table-column field="exptime" label="Exptime" sortable v-slot="props">{{
              props.row.exptime
            }}
          </b-table-column>
          <b-table-column field="public_url" label="URL" v-slot="props">
            <b-button tag="a" :href="props.row.public_url" type="is-link is-light is-small">.FITS</b-button>
          </b-table-column>
          <b-table-column field="status" label="Status" sortable v-slot="props">
            <b-tag type="is-success is-uppercase">{{ props.row.status }}</b-tag>
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
    images: db.collection('images').orderBy('time', 'desc').limit(25)
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
