<template>
  <div>
    <section>
      <b-modal :active.sync="isSearchFormActive"
               has-modal-card
               trap-focus
               aria-role="dialog"
               aria-modal>
          <SourcesSearch></SourcesSearch>
      </b-modal>
      <section>
      <h1 class="is-size-4" v-if="!fromSearch">Recently Processed</h1>
      <hr >
      </section>
      <nav class="level">
        <div class="level-left">
          <div class="level-item">
            <form v-on:submit.prevent="submitForm">
              <b-field>
                  <b-input
                      v-model="gotoPicid"
                      placeholder="PICID">
                  </b-input>
                <button class="button is-primary"
                    @click="submitForm">
                    <b-icon icon="chevron-right"></b-icon>
                </button>
              </b-field>
            </form>
          </div>
        </div>
        <div class="level-right">
          <div class="level-item">
            <button class="button is-primary is-pulled-right"
                @click="isSearchFormActive = true">
                Search Sources
            </button>
          </div>
        </div>
      </nav>
    </section>
    <b-table
      :data="sourceRows"
      :columns="columns"
      :loading="isSearching"
      :narrowed=true
      :bordered=true
      :striped=true
      :hoverable=true
      :focusable=true
      :mobile-cards=true
      :paginated=true
      :current-page.sync="currentPage"
      :per-page=10
      >
      <template slot-scope="props">
          <b-table-column field="id" label="PICID" width="50" sortable>
            <template slot="header" slot-scope="{ column }">
              <b-tooltip label="PANOPTES Input Catalog ID" dashed>
              {{ column.label }}
              </b-tooltip>
            </template>
            <router-link
              :to="{ name: 'sourceDetail', params: { picid: props.row.id }}">
            {{ props.row.id }}
            </router-link>
          </b-table-column>
          <b-table-column field="ra" label="RA [deg]" width="5" sortable numeric>
            {{ props.row.ra.toFixed(3) }}
          </b-table-column>
          <b-table-column field="dec" label="Dec [deg]" width="5" sortable numeric>
            {{ props.row.dec.toFixed(3) }}
          </b-table-column>
          <b-table-column v-if="fromSearch" field="distance" label="Distance [deg]" width="5" sortable numeric>
            {{ props.row.distance.toFixed(3) }}
          </b-table-column>
          <b-table-column field="class" label="Class" width="20" sortable>
            {{ props.row.lumclass }}
          </b-table-column>
          <b-table-column field="vmag" label="Vmag" width="5" sortable numeric>
            {{ props.row.vmag.toFixed(2) }}
          </b-table-column>
          <b-table-column field="id" label="Info" width="5">
            <a v-bind:href="'https://exofop.ipac.caltech.edu/tess/target.php?id=' + props.row.id" target="_blank">
              ExoFOP
            </a>
          </b-table-column>
      </template>
    </b-table>
    <div class="is-pulled-right"> Total Rows: {{ sourceRows.length }} </div>
  </div>
</template>

<script>
import { mapState, mapActions } from 'vuex'

import { SourcesService } from '../services/SourcesService.js'
import SourcesSearch from '@/components/SourcesSearch'

let sources = new SourcesService()

export default {
  name: 'Sources',
  components: {
    SourcesSearch
  },
  computed: {
    ...mapState([
      'fromSearch',
      'sourceRows',
      'searchModel',
      'isSearching'
    ])
  },
  methods: {
    submitForm: function() {
      this.$store.dispatch('setSource', this.gotoPicid);
      this.$router.push({ name: 'sourceDetail', params: { picid: this.gotoPicid }});
    }
  },
  created () {
    // Look up the most recent sources.
    this.$store.dispatch('getRecentSources');
  },
  data () {
    return {
      perPage: 10,
      currentPage: 1,
      loading: false,
      gotoPicid: null,
      isSearchFormActive: false,
      sources: sources,
      filter: null,
      columns: []
    }
  }
}
</script>

<style scoped="">
.button {
  margin-bottom: 15px;
}
</style>
