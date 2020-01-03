<template>
  <div>
    <vue-good-table
      :columns="fields"
      :rows="rows"
      :pagination-options="{
        enabled: true,
        mode: 'pages',
        perPage: this.perPage
      }"
      styleClass="vgt-table striped bordered condensed"
    >
    <template slot="table-row" slot-scope="props">
      <span v-if="props.column.key == 'picid'">
        <router-link
          :to="{ name: 'sourceDetail', params: { picid: props.row.id, info: props.row }}">
          {{ props.row.id }}
        </router-link>
      </span>
      <span v-else-if="props.column.key == 'info'">
        <a v-bind:href="'https://exofop.ipac.caltech.edu/tess/target.php?id=' + props.row.id" target="_blank">
          ExoFOP
        </a>
      </span>
      <span v-else>
        {{props.formattedRow[props.column.field]}}
      </span>
    </template>
  </vue-good-table>
  </div>
</template>

<script>
import { SourcesService } from '../services/SourcesService.js'

let sources = new SourcesService()

export default {
  name: 'Sources',
  components: {
  },
  methods: {
    roundVal : function(value) {
      return Number(value).toFixed(3);
    }
  },
  created () {
    this.sources.getRecent().then((response) => {
      if (response.status == 200){
        this.rows = response.data.picid;
      }
      })
      .catch((err) => {
        console.log('Error getting documents', err);
      })
      .finally(() => (this.loading = false));
  },
  data () {
    return {
      perPage: 10,
      currentPage: 0,
      sources: sources,
      filter: null,
      rows: [],
      fields: [
        { label: 'PICID', field: 'id', key: 'picid', sortable: true, filterOptions: { enabled: true } },
        {
          label: 'RA',
          field: 'ra',
          sortable: true,
          filterOptions: { enabled: true },
          formatFn: this.roundVal,
        },
        {
          label: 'Dec',
          field: 'dec',
          sortable: true,
          filterOptions: { enabled: true },
          formatFn: this.roundVal,
        },
        {
          label: 'Class',
          field: 'lumclass',
          sortable: true,
          filterOptions: { enabled: true }
        },
        {
          label: 'Vmag',
          field: 'vmag',
          sortable: true ,
          formatFn: this.roundVal,
        },
        { label: 'Info', field: 'id', key: 'info' }
      ]
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
a {
  color: #42b983;
}
</style>
