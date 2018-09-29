<template>
  <div>
  <vuetable ref="vuetable"
    @vuetable:pagination-data="onPaginationData"
    api-url="http://127.0.0.1:8080/observations"
    :css="css.table"
    :fields="[
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
    },
    { name: 'pocs_version', title: 'POCS Version' },
    { name: 'piaa_state', title: 'State' },
    { name: 'exp_time', title: 'Exposure Time' },
    { name: 'image_count', title: 'Images' },
    ]"
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
import VuetablePaginationMixin from 'vuetable-2';
import VuetableCss from './VuetableBootstrapConfig.js';

export default {
  components: {
    Vuetable,
    VuetablePaginationMixin
  },
  data() {
    return {
      css: VuetableCss,
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
