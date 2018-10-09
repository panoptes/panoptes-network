<template>
<nav class="panel">
  <p class="panel-heading">
    {{ sequenceId.split('_').join(' ') }}
  </p>
  <div class="panel-block">
    <b-tabs
      style="width: 100%"
      v-model="activeTab" 
      position="is-centered" 
      type="is-boxed">
      <b-tab-item label="Info">
        Hi
      </b-tab-item>

      <b-tab-item label="Images">
        <b-table 
          :data="rows" 
          :bordered="true"
          :striped="true"
          :narrowed="true"
          :hoverable="true"
          default-sort="date_obs"
        >
            <template slot-scope="props">
                <b-table-column field="date_obs" label="Date" sortable date>
                  {{ new Date(props.row.date_obs) | moment("YYYY-MM-DD hh:mm:ss") }}
                </b-table-column>

                <b-table-column field="airmass" label="Airmass" sortable numeric>
                    {{ props.row.airmass }}
                </b-table-column>

                <b-table-column field="exp_time" label="Exptime" numeric>
                    {{ props.row.exp_time }}
                </b-table-column>                

                <b-table-column field="iso" label="ISO" numeric>
                    {{ props.row.iso }}
                </b-table-column>

                <b-table-column field="moon_separation" label="Moon Sep" numeric>
                    {{ props.row.moon_separation }}
                </b-table-column>                

                <b-table-column field="moon_fraction" label="Moon Frac" numeric>
                    {{ props.row.moon_fraction }}
                </b-table-column>

                <b-table-column field="file_path" label="Image" centered>
                  <a 
                  :href="props.row.file_path | toJpg" 
                  target="_blank"
                  v-if="props.row.file_path" 
                  >
                    [click]
                  </a>
                </b-table-column>                

            </template>        
        </b-table>
      </b-tab-item>

      <b-tab-item label="Timelapse">
        <video
          ref="videoRef"
          v-bind:src="timelapseUrl"
          id="video-container"
          width="50%"
          controls></video>        
      </b-tab-item>
    </b-tabs>
  </div>  
</nav>
</template>

<script>
import { ObservationsService } from '../services/ObservationsService.js'
import ImagePreview from '@/components/ImagePreview'

const baseUrl = 'https://storage.googleapis.com/panoptes-survey'

let observations = new ObservationsService()

export default {
  name: 'ObservationDetail',
  components: {
    ImagePreview
  },
  methods: {
  },
  created () {
    this.observations.getObservation(this.sequenceId).then(response => {
      this.rows = response.data.data
      this.files = response.data.sequence_files
      this.images = this.files.jpg
      this.sequenceDir = response.data.sequence_dir
      this.thumbUrl = this.files.jpg[0]
      this.timelapseUrl = this.files.mp4[0]
      this.$refs.videoRef.src = this.timelapseUrl
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
      activeTab: 1,
      isImageModalActive: false,
      info: null,
      observations: observations,
      files: [],
      images: [],
      sequenceDir: '',
      baseUrl: baseUrl,
      thumbUrl: '',
      timelapseUrl: '',
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
