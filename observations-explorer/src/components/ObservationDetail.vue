<template>
  <div>
    <h2>{{ $route.params.id }}</h2>

    : {{ thumbUrl }} :
    <hr>
    : {{ files }} :
    <hr>
    <img v-bind:src="thumbUrl" width="200px"/>
    <lightbox
        v-if="thumbUrl"
        thumbnail=this.thumbUrl
        :images=this.files.jpg
    >
        <lightbox-default-loader slot="loader"></lightbox-default-loader> <!-- If you want to use built-in loader -->
        <!-- <div slot="loader"></div> --> <!-- If you want to use your own loader -->
    </lightbox>

    <!-- <video ref="videoRef" src="" id="video-container" width="25%" controls></video> -->

    <vue-good-table
      :columns="columns"
      :rows="rows"
      :line-numbers="true"
      :pagination-options="{
        enabled: true
      }"
      :sort-options="{
        enabled: true,
        initialSortBy: {field: 'start_date', type: 'desc'}
      }"
    >
    </vue-good-table>
  </div>
</template>

<script>
import { VueGoodTable } from 'vue-good-table'
import 'vue-good-table/dist/vue-good-table.css'
import Lightbox from 'vue-pure-lightbox'

import { ObservationsService } from '../services/ObservationsService.js'
let observations = new ObservationsService()

export default {
  name: 'ObservationDetail',
  components: {
    VueGoodTable,
    Lightbox
  },
  methods: {
    formatImagelink: function (value) {
      return value
    }
  },
  created () {
    this.observations.getObservation(this.$route.params.id).then(response => {
      this.rows = response.data.data
      this.files = response.data.sequence_files
      this.sequenceDir = response.data.sequence_dir
      // this.thumbUrl = this.baseUrl + '/' + this.sequenceDir + '/' + this.files.jpg[0]
      // this.timelapseUrl = this.baseUrl + '/' + this.sequenceDir + '/' + this.files.mp4[0]
      // this.$refs.videoRef.src = this.timelapseUrl
    })
      .catch(error => {
        console.log(error)
      })
      .finally(() => (this.loading = false))
  },
  data () {
    return {
      info: null,
      observations: observations,
      files: [],
      sequenceDir: '',
      baseUrl: 'https://storage.googleapis.com/panoptes-survey',
      timelapseUrl: '',
      columns: [
        {
          label: 'Time',
          field: 'date_obs',
          type: 'date',
          dateInputFormat: 'YYYY-MM-DDTHH:mm:ss',
          dateOutputFormat: 'MM-DD HH:mm:ss'
        },
        { label: 'RA', field: 'center_ra', type: 'number' },
        { label: 'Dec', field: 'center_dec', type: 'number' },
        { label: 'Moon Frac', field: 'moon_fraction', type: 'number' },
        { label: 'Moon Sep', field: 'moon_separation', type: 'number' },
        {
          label: 'Image',
          field: 'id',
          formatFn: this.formatImagelink
        }
      ],
      rows: []
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
h1, h2 {
  font-weight: normal;
}
a {
  color: #42b983;
}
</style>
