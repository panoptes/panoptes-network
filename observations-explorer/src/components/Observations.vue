<template>
  <div>
  <vuetable ref="vuetable"
    @vuetable:pagination-data="onPaginationData"
    api-url="http://127.0.0.1:8080/observations"
    :sort-order="sortOrder"
    :css="css.table"
    :fields="fields"
    data-path="data"
    pagination-path="links.pagination"
  ></vuetable>
  <vuetable-pagination ref="pagination"
    @vuetable-pagination:change-page="onChangePage"
    :css="css.pagination"
  ></vuetable-pagination>
  </div>
</template>

<script>
import Vuetable from 'vuetable-2';
import VuetablePagination from 'vuetable-2';
import VuetableCss from './VuetableBootstrapConfig.js';

export default {
  components: {
    Vuetable,
    VuetablePagination
  },
  data() {
    return {
      fields: [
        { 
            name: 'unit_id', 
            title: 'Unit',
            sortField: 'unit_id',
            formatter (value) {
              // Silly padding
              var unit_id = 'PAN000';
              var l = -1 * value.toFixed(0).length;
              unit_id = unit_id.slice(0, l) + value;
              return unit_id;
            },
        },
        { 
          name: 'id', 
          title: 'Sequence ID',
          sortField: 'unit_id'
        },
        { name: 'start_date', title: 'Date', sortField: 'start_date' },
        { name: 'pocs_version', title: 'POCS Version', sortField: 'pocs_version' },
        { name: 'piaa_state', title: 'State', sortField: 'piaa_state' },
        { name: 'exp_time', title: 'Exposure Time', sortField: 'exp_time' },
        { name: 'image_count', title: 'Images', sortField: 'image_count' },
      ],
      css: VuetableCss,
      sortOrder: [
        {
          field: 'start_date',
          direction: 'desc'
        }
      ],
    }
  },
  methods: {
    onPaginationData (paginationData) {
      this.$refs.pagination.setPaginationData(paginationData);
    },
    onChangePage (page) {
      this.$refs.vuetable.changePage(page);
    }
  }
};
</script>
