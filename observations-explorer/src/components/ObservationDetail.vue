<template>
<b-card>
  <b-tabs card>
    <b-tab title="info" active>
      <b-card header="<b>Info</b>">
        <ObservationSummary 
          :sequence="sequence"
          :sequenceDir="sequenceDir"
        />
      </b-card>
      <b-card 
        no-body
        :header="'<b>Images <small>(' + images.length + ')</small></b>'"
        >
        <b-card-body>
          <b-table 
            :items="images" 
            :fields="fields"
            :per-page="perPage"
            :current-page="currentPage"
            sort-by="obstime"
            :sort-desc=false
            caption-top
            bordered
            striped
            narrowed
            hoverable
            small
          >
          <template slot="obstime" slot-scope="data">
            {{ data.value | moment("HH:mm:ss") }}
          </template>                            
          <template slot="file_path" slot-scope="data">
            <b-link 
              v-if="jpg_files"
              :href="data.value | toJpg" target="_blank" 
              >
              <font-awesome-icon icon="image"></font-awesome-icon>
            </b-link>
            </a>
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
import { ObservationsService } from '../services/ObservationsService.js'
import ObservationSummary from '@/components/ObservationSummary'

const baseUrl = 'https://storage.googleapis.com/panoptes-survey'

let observations = new ObservationsService()

export default {
  name: 'ObservationDetail',
  components: {
    ObservationSummary
  },
  methods: {
  },
  created () {
    this.observations.getObservation(this.sequenceId).then(response => {
      this.info = response.data.items

      this.sequence = this.info.sequence
      this.sequenceDir = this.info.sequence_dir
      this.images = this.info.images

      this.files = this.info.sequence_files
      if (this.files !== undefined) {
        this.jpg_files = this.files.jpg
        this.thumbUrl = this.files.jpg[0]
        this.timelapseUrl = this.files.mp4[0]
      } else {
        this.files = []
      }
    })
      .catch(error => {
        this.$router.replace({ name: 'home' })
      })
      .finally(() => (this.loading = false))
  },
  filters: {
    toJpg: function (value) {
      return value.replace(".fits.fz", ".jpg")
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
        { label: 'Time', key: 'obstime', sortable: true },
        { label: 'HA', key: 'ha_mnt', sortable: true },
        { label: 'RA', key: 'ra_mnt', sortable: true },
        { label: 'Dec', key: 'dec_mnt', sortable: true },
        { label: 'Exptime', key: 'exptime', sortable: true },
        { label: 'State', key: 'state', sortable: true },
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
