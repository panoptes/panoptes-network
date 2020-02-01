<template>
  <nav class="panel is-pulled-left">
    <p v-if="sourceRecord !== null" class="panel-heading">
      PICID: {{ picid }} ({{ sourceRecord.ra.toFixed(3) }}
      {{ sourceRecord.dec > 0 ? '+' : '-' }}{{ sourceRecord.dec.toFixed(3) }})
      Vmag={{ sourceRecord.vmag.toFixed(3) }}
    </p>
    <b-table
      :data="observations"
      :columns="columns"
      :narrowed="true"
      :striped="true"
      :selected.sync="selected"
    >
      <template slot-scope="props">
        <b-table-column
          field="sequence_id"
          label="Sequence ID"
          width="50"
          sortable
          searchable
        >
          <router-link
            :to="{
              name: 'observationDetail',
              params: { sequenceId: props.row.sequence_id, info: props.row }
            }"
          >
            {{ props.row.sequence_id }}
          </router-link>
        </b-table-column>
        <b-table-column field="notes" label="Notes" width="20" sortable>
          {{ props.row.notes }}
        </b-table-column>
        <b-table-column
          field="observation_start_time"
          label="Obs Start Time"
          width="5"
          sortable
          searchable
          numeric
        >
          {{ props.row.observation_start_time }}
        </b-table-column>
        <b-table-column
          field="observation_end_time"
          label="Obs End Time"
          width="5"
          sortable
          searchable
          numeric
        >
          {{ props.row.observation_end_time }}
        </b-table-column>
        <b-table-column field="id" label="PIAA Doc ID" searchable>
          {{ props.row.id }}
        </b-table-column>
        <b-table-column
          field="piaa_document_id"
          label="PIAA ID"
          width="5"
          sortable
          numeric
        >
          >
          {{ props.row.piaa_document_id }}
        </b-table-column>
      </template>
      <template slot="empty">
        <section class="section">
          <div class="content has-text-grey has-text-centered">
            <p>
              <b-icon pack="fas" icon="rocket" size="is-large" />
            </p>
            <p>Nothing here.</p>
          </div>
        </section>
      </template>
    </b-table>
  </nav>
</template>

<script>
import { mapState } from 'vuex'

export default {
  name: 'PiaaList',
  watch: {
    selected: function(row) {
      this.$store.dispatch('selectRow', row)
    }
  },
  computed: {
    ...mapState(['picid', 'observations', 'sourceRecord'])
  },
  data() {
    return {
      loading: true,
      selected: {},
      columns: []
    }
  }
}
</script>
