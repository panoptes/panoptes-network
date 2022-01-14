<template>
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
               per-page="10"
               sort-icon="arrow-up"
               detailed
               detail-key="id"
      >
        <b-table-column field="time" label="Date" sortable v-slot="props">
          {{ props.row.time.toDate().toLocaleString() }}
        </b-table-column>
        <b-table-column field="id" label="Unit" sortable v-slot="props">{{ props.row.id.split('_')[0] }}</b-table-column>
        <b-table-column field="id" label="Camera" sortable v-slot="props">{{ props.row.id.split('_')[1] }}</b-table-column>
<!--        <b-table-column field="id" label="ID" sortable v-slot="props">{{ props.row.id }}</b-table-column>-->
        <b-table-column field="coords" label="Coords" sortable v-slot="props">
          <span v-if="props.row.coordinates.ra">
            {{ props.row.coordinates.ra.toFixed(3) }}°
            {{ props.row.coordinates.dec.toFixed(3) }}°
          </span>
        </b-table-column>
        <b-table-column field="exptime" label="Exptime" sortable v-slot="props">{{
            props.row.camera.exptime
          }}
        </b-table-column>
        <b-table-column field="public_url" label="URL" v-slot="props">
          <b-button tag="a"
                    :href="base_url + '/' + props.row.uid.replaceAll('_', '/') + '/image.fits.fz'"
                    type="is-link is-light is-small">.FITS
          </b-button>
        </b-table-column>
        <b-table-column field="num_sources" label="Sources" v-slot="props">
          {{ props.row.sources.num_detected }}
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
</template>

<script>
import {db} from "../db";

export default {
  name: 'RecentImages',
  data() {
    return {
      base_url: 'https://storage.googleapis.com/panoptes-images-processed',
      images: [],
    }
  },
  firestore: {
    images: db.collectionGroup('images').orderBy('time', 'desc').limit(50)
  },
  methods: {}
}
</script>

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
