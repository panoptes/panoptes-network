<template>
  <section class="section">
    <div class="columns">
      <div class="column is-two-thirds">
        <div v-if="piaaRecord !== null">
          <pre>{{ piaaRecord.rms }}</pre>
        </div>
        <PiaaList />
        }
      </div>
      <div class="column">
        <PSCPlot />
      </div>
    </div>
    <div class="columns">
      <div class="column">
        <b-tabs
          @change="switchTab"
          type="is-toggle"
          >
          <b-tab-item label="Data">
            <LightcurvePlot />
            }
          </b-tab-item>
          <b-tab-item label="Raw Flux">
            <RawCountPlot />
          </b-tab-item>
          <b-tab-item label="Ref Locations">
            <ReferenceLocationsPlot />
          </b-tab-item>
    <!--         <b-tab-item label="Ref Distances" v-if="sourceRunDetail.files.plots">
            <a :href="sourceRunDetail.files.plots['reference-pairplot']" target="_blank">
              <b-img :src="sourceRunDetail.files.plots['reference-pairplot']"></b-img>
            </a>
          </b-tab-item>
          <b-tab-item label="Coeffs" v-if="sourceRunDetail.files.plots">
            <a :href="sourceRunDetail.files.plots['reference-scores']" target="_blank">
              <b-img :src="sourceRunDetail.files.plots['reference-scores']"></b-img>
            </a>
            <a :href="sourceRunDetail.files.plots['reference-coeffs']" target="_blank">
              <b-img :src="sourceRunDetail.files.plots['reference-coeffs']"></b-img>
            </a>
          </b-tab-item> -->
          <b-tab-item label="Pixel Drift">
            <PixelDriftPlot />
          </b-tab-item>
    <!--         <b-tab-item label="Ref Vmags" v-if="sourceRunDetail.files.plots">
            <a :href="sourceRunDetail.files.plots['reference-vmags']" target="_blank">
              <b-img :src="sourceRunDetail.files.plots['reference-vmags']">
              </b-img>
            </a>
          </b-tab-item> -->
          <b-tab-item label="Files" v-if="sourceRunDetail">
            <ul>
              <li v-for="file in sourceRunDetail.files">
                <a :href="file">{{ file }}</a>
              </li>
            </ul>
          </b-tab-item>
        </b-tabs>
      </div>
    </div>
  </section>

</template>

<script>
import { mapState, mapActions } from 'vuex'

import LightcurvePlot from './SourceDetail/LightcurvePlot.vue'
import RawCountPlot from './SourceDetail/RawCountPlot.vue'
import PixelDriftPlot from './SourceDetail/PixelDriftPlot.vue'
import ReferenceLocationsPlot from './SourceDetail/ReferenceLocationsPlot.vue'
import PSCPlot from './SourceDetail/PSCPlot.vue'

import PiaaList from './PiaaList.vue'

export default {
  name: 'SourceDetail',
  components: {
    LightcurvePlot,
    RawCountPlot,
    PixelDriftPlot,
    ReferenceLocationsPlot,
    PSCPlot,
    PiaaList
  },
  methods: {
    roundVal : function(value) {
      return Number(value).toFixed(3);
    },
    leadingZeros : function(num) {
      var size = 3;
      var s = String(num);
      while (s.length < (size || 2)) {s = "0" + s;}
      return s;
    },
    switchTab: function(tabIndex){
      switch(tabIndex){
        case 0:
          this.$store.dispatch('getLightcurve');
          break;
        case 1:
          this.$store.dispatch('getRawCounts');
          break
        case 2:
          this.$store.dispatch('getReferenceLocations');
          break;
        case 3:
          this.$store.dispatch('getPixelDrift');
          break;
      }
    },
    ...mapActions([
      'setSource'
    ])
  },
  filters: {
    roundVal : function(value) {
      return Number(value).toFixed(3);
    },
    leadingZeros : function(num) {
      var size = 3;
      var s = String(num);
      while (s.length < (size || 2)) {s = "0" + s;}
      return s;
    }
  },
  computed: {
    ...mapState([
      'picid',
      'observations',
      'sourceRecord',
      'sourceRunDetail',
      'piaaRecord',
      'locationData',
      'rawData',
      'pixelData',
      'frameIndex'
    ])
  },
  created () {
    // Check to see if store has the picid set.
    if (this.picid === null || this.sourceRecord === null){
      this.setSource(this.$route.params.picid);
    }
  },
  data () {
    return {
      loading: true
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
.header {
  font-size: 0.9rem;
}
h1, h2 {
  font-weight: normal;
}
a {
  color: #42b983;
}
table th {
  text-align: center;
}
.list-group {
  max-height: 300px;
  margin-bottom: 10px;
  overflow: scroll;
  -webkit-overflow-scrolling: touch;
}

</style>
