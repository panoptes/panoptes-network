<template>
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
               per-page="10"
               sort-icon="arrow-up"
               detailed
               detail-key="id"
      >
        <b-table-column field="time" label="Date (UTC)" sortable v-slot="props">
          {{ props.row.time.toDate().toLocaleString() }}
        </b-table-column>
        <b-table-column field="id" label="Unit" sortable v-slot="props">{{ props.row.id.split('_')[0] }}</b-table-column>
        <b-table-column field="id" label="Camera" sortable v-slot="props">{{ props.row.id.split('_')[1] }}</b-table-column>
        <b-table-column field="id" label="ID" sortable v-slot="props">{{ props.row.id }}</b-table-column>
        <b-table-column field="field_name" label="Field name" sortable v-slot="props">{{
            props.row.field_name
          }}
        </b-table-column>
        <b-table-column field="coords" label="RA/Dec (deg)" sortable v-slot="props">
            <span v-if="props.row.coordinates.mount_ra">
              {{ props.row.coordinates.mount_ra.toFixed(2) }}° {{ props.row.coordinates.mount_dec.toFixed(2) }}°
            </span>
        </b-table-column>
        <b-table-column field="num_images" label="Images" sortable v-slot="props">{{
            props.row.num_images
          }}
        </b-table-column>
        <b-table-column field="total_minutes_exptime" label="Total minutes" sortable v-slot="props">
          {{ (props.row.total_exptime / 60).toFixed(2) }}
        </b-table-column>
        <b-table-column field="status" label="Status" sortable v-slot="props">
          <b-tag
              v-if="props.row.status"
              :type="{
                'is-primary': props.row.status == 'CREATED',
                'is-warning': props.row.status == 'PROCESSING',
                'is-success': props.row.status == 'PROCESSED',
                'is-danger': (props.row.status == 'TOO_MUCH_DRIFT' || props.row.status == 'NOT_ENOUGH_FRAMES'),

              }"
          >{{ props.row.status }}
          </b-tag>
        </b-table-column>
        <template #detail="props">
          <b-tabs>
            <b-tab-item v-if="props.row.urls && props.row.urls.includes('stack.png')" label="Stack Image">
              <b-image
                  :src="base_url + '/' + props.row.sequence_id.replaceAll('_', '/') + '/stack.png'"
                  alt="Stacked image"
              ></b-image>
            </b-tab-item>
            <b-tab-item v-if="props.row.urls && props.row.urls.includes('diff.png')" label="Diff Image">
              <b-image
                  :src="base_url + '/' + props.row.sequence_id.replaceAll('_', '/') + '/diff.png'"
                  alt="Stacked image"
              ></b-image>
            </b-tab-item>
            <b-tab-item v-if="props.row.urls && props.row.urls.includes('processing-observation.html')"
                        label="Notebook">
              <b-button tag="a"
                        :href="base_url + '/' + props.row.sequence_id.replaceAll('_', '/') + '/processing-observation.html'"
                        target="_blank" type="is-link is-light is-small">Notebook
              </b-button>
              <iframe
                  :src="base_url + '/' + props.row.sequence_id.replaceAll('_', '/') + '/processing-observation.html'"
                  width="100%" height="600px"
                  frameborder="0"></iframe>
            </b-tab-item>
            <b-tab-item label="Raw">
              <pre>
              {{ props.row }}
              </pre>
            </b-tab-item>
          </b-tabs>
        </template>
      </b-table>
    </div>
  </div>
</template>

<script>
import {db} from "../db";

export default {
  name: 'Observations',
  data() {
    return {
      base_url: 'https://storage.googleapis.com/panoptes-images-processed',
      observations: [],
    }
  },
  firestore: {
    observations: db.collectionGroup('observations').where('time', '>', new Date('2019-01-01')).orderBy('time', 'desc').limit(25)
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
