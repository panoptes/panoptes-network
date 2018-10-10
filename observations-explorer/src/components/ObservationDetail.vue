<template>
<b-card>
  <b-tabs card>
    <b-tab title="info" active>
      <b-card-group deck>
        <b-card header="<b>Info</b>">
          <ObservationSummary 
            :sequence="sequence"
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
              sort-by="date_obs"
              :sort-desc=false
              caption-top
              bordered
              striped
              narrowed
              hoverable
              small
            >
            <template slot="date_obs" slot-scope="data">
              {{ data.value | moment("HH:mm:ss") }}
            </template>            
            <template slot="center_ra" slot-scope="data">
              {{ data.value }}
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
            <b-col cols="12">
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
      </b-card-group>      
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
        console.log(error)
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
        { label: 'Time', key: 'date_obs', sortable: true },
        { label: 'Airmass', key: 'airmass', sortable: true },
        { label: 'ISO', key: 'iso', sortable: true },
        { label: 'Moon Sep', key: 'moon_separation', sortable: true },
        { label: 'Moon Frac', key: 'moon_fraction', sortable: true },
        { label: 'Exp Time', key: 'exp_time', sortable: true },
        { label: 'Center', key: 'center_ra', sortable: true },
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
