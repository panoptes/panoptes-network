<template>
  <nav class="panel is-pulled-left">
    <p class="panel-heading">PICID List</p>
    <div class="panel-block">
      <b-table
        :data="rows"
        :columns="fields"
        :striped=true
        :bordered=true
        :narrowed=true
        :hoverable=true
        :paginated=true
        :per-page="perPage"
        :current-page.sync="currentPage"
        :pagination-simple="isPaginationSimple"
        :pagination-position="paginationPosition"
        :default-sort-direction="defaultSortDirection"
        :sort-icon="sortIcon"
        :sort-icon-size="sortIconSize"
        aria-next-label="Next page"
        aria-previous-label="Previous page"
        aria-page-label="Page"
        aria-current-label="Current page"
        :selected.sync="selected"
        >
        <template slot-scope="props">
          <b-table-column field="id" label="PICID" width="50" sortable searchable>
            {{ props.row.id }}
          </b-table-column>
          <b-table-column field="lumclass" label="Class" width="20" sortable>
            {{ props.row.lumclass }}
          </b-table-column>
          <b-table-column field="ra" label="RA" width="5" sortable searchable numeric>
            {{ props.row.ra.toFixed(3) }}
          </b-table-column>
          <b-table-column field="dec" label="Dec" width="5" sortable searchable numeric>
            {{ props.row.dec.toFixed(3) }}
          </b-table-column>
          <b-table-column field="vmag" label="Vmag" width="5" sortable numeric>
            {{ props.row.vmag.toFixed(3) }}
          </b-table-column>
          <b-table-column field="id" label="." width="10">
            <a :href="'https://exofop.ipac.caltech.edu/tess/target.php?id=' + props.row.id" target="_blank">
            <b-icon
                pack="fas"
                icon="external-link-alt"
                size="is-small">
            </b-icon>
            </a>
          </b-table-column>
        </template>
        </b-table>
    </div>
  </nav>
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
  watch: {
    selected: function(row) {
      this.$store.dispatch('setSource', row.id);
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
      sources: sources,
      selected: {},
      rows: [],
      isPaginationSimple: false,
      paginationPosition: 'bottom',
      defaultSortDirection: 'asc',
      sortIcon: 'arrow-up',
      sortIconSize: 'is-small',
      currentPage: 1,
      perPage: 5,
      fields: [
        {
          label: 'PICID',
          field: 'id',
          'custom-key': 'picid',
          width: 20,
          sortable: true,
          searchable: true
        },
        {
          label: 'Class',
          field: 'lumclass',
          width: 20,
          sortable: true,
          searchable: true
        },
        {
          label: 'RA',
          field: 'ra',
          numeric: true,
          sortable: true,
          searchable: true
        },
        {
          label: 'Dec',
          field: 'dec',
          numeric: true,
          sortable: true,
          searchable: true
        },
        {
          label: 'Vmag',
          field: 'vmag',
          numeric: true,
          sortable: true
        },
        {
          label: 'ID',
          field: 'id',
          'custom-key': 'id',
          width: 10
        }
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
