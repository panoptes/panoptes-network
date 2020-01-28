<template>
<b-card>
  <b-tabs card>
    <b-tab title="info" active>
      <b-card header="Info">
        <ObservationSummary
          :sequence="sequence"
          :sequenceDir="sequenceDir"
        />
      </b-card>
      <b-card
        no-body
        :header="'Images (' + images.length + ')'"
        >
        <b-card-body>
          <b-table
            :items="images"
            :fields="fields"
            :per-page="perPage"
            :current-page="currentPage"
            sort-by="imgtime"
            :sort-desc=false
            caption-top
            bordered
            striped
            narrowed
            hoverable
            small
          >
          <template v-slot:cell(imgtime)="data">
            {{ data.value | moment("HH:mm:ss") }}
          </template>
          <template v-slot:cell(airmass)="data">
            {{ data.value | roundVal }}
          </template>
          <template v-slot:cell(file_path)="data">
            FITS:
              <b-link
              v-if="jpg_files"
              :href="data.value.replace('.fits.fz', '_r.fits').replace()" target="_blank"
              >R </b-link>

            <b-link
              v-if="jpg_files"
              :href="data.value.replace('.fits.fz', '_g.fits')" target="_blank"
              >G </b-link>

            <b-link
              v-if="jpg_files"
              :href="data.value.replace('.fits.fz', '_b.fits')" target="_blank"
              >B </b-link>
              JPG
            <b-link
              v-if="jpg_files"
              :href="data.value.replace('.fits.fz', '.jpg')" target="_blank"
              >
              <font-awesome-icon icon="image"></font-awesome-icon>
            </b-link>
          </template>
        </b-table>
        <b-row>
          <b-col cols="6">
            <b-button size='sm' variant='link'>
              <a :href='"http://us-central1-panoptes-survey.cloudfunctions.net/observation-file-list?sequence_id=" + sequenceId'>Download file list</a>
            </b-button>
            <font-awesome-icon icon="question-circle" id="downloadList"></font-awesome-icon>

          </b-col>
          <b-popover target="downloadList" triggers="hover focus" delay="500">
             <template slot="title">Download File List</template>
             Clicking this link will download a text file that contains a list
             of FITS files for this observation.

             You can use a tool like <code>wget</code> or <code>curl</code> to download
             the files:
             <br/><br/>
             <code>wget -i {{sequenceId}}.txt</code>
          </b-popover>
          <b-col cols="6">
            <b-pagination
              :total-rows="images.length"
              :per-page="perPage"
              v-model="currentPage"
              class="float-right"
               />
          </b-col>
        </b-row>
        </b-card-body>
      </b-card>
    </b-tab>
    <b-tab
      title="timelapse"
      :disabled="timelapseUrl == ''"
      >
      <b-embed
        type="video"
        controls
        :src="timelapseUrl"
      >
      </b-embed>
    </b-tab>
  </b-tabs>
</b-card>
</template>

<script>
import { mapState, mapActions } from 'vuex'

import ObservationSummary from '@/components/ObservationSummary'

const baseUrl = 'https://storage.googleapis.com/panoptes-survey'

export default {
  name: 'ObservationDetail',
  components: {
    ObservationSummary
  },
  computed: {
    ...mapState([
      'units',
      'fromSearch',
      'sourceRows',
      'searchModel',
      'observations',
      'isSearching'
    ])
  },
  // created () {
  //   this.observations.getObservation(this.sequenceId).then(response => {
  //     this.info = response.data.items

  //     this.sequence = this.info.sequence
  //     this.sequenceDir = this.info.sequence_dir
  //     this.images = this.info.images

  //     this.files = this.info.sequence_files
  //     if (this.files !== undefined) {
  //       if (this.files.jpg){
  //         this.jpg_files = this.files.jpg
  //         this.thumbUrl = this.files.jpg[0]
  //       }
  //       this.timelapseUrl = ''
  //       if (this.files.mp4) {
  //         this.timelapseUrl = this.files.mp4[0]
  //       }
  //     } else {
  //       this.files = []
  //     }
  //   })
  //     .catch(error => {
  //       this.$router.replace({ name: 'home' })
  //     })
  //     .finally(() => (this.loading = false))
  // },
  filters: {
    roundVal : function(value) {
      return Number(value).toFixed(3);
    }
  },
  data () {
    return {
      sequenceId: this.$route.params.sequenceId,
      info: {},
      sequence: {},
      sequenceDir: '',
      images: [],
      files: [],
      jpg_files: [],
      activeTab: 0,
      perPage: 10,
      currentPage: 1,
      isImageModalActive: false,
      observations: observations,
      baseUrl: baseUrl,
      thumbUrl: '',
      timelapseUrl: '',
      fields: [
        { label: 'Time', key: 'imgtime', sortable: true },
        { label: 'HA', key: 'ha_mnt', sortable: true },
        { label: 'Airmass', key: 'airmass', sortable: true },
        { label: 'Exptime', key: 'exptime', sortable: true },
        { label: 'Image', key: 'file_path', sortable: false, tdClass: 'text-center' }
      ]
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
table th {
  text-align: center;
}
</style>
