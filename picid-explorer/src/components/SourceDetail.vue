<template>
  <b-container class="observations">
    <b-row> <a href="/piaa">PICID List</a> </b-row>
    <b-row class="header" no-gutters>
      <b-col>
          <b-card :title="'PICID: ' + picid">
            <b-card-text v-if="sourceRecord">
              Vmag: {{ sourceRecord.vmag | roundVal }} <br>
              Coords: {{ sourceRecord.ra | roundVal }}° {{ sourceRecord.dec | roundVal }}° <br>
              Class: {{ sourceRecord.lumclass }} <br>
              <a :href="'https://exofop.ipac.caltech.edu/tess/target.php?id=' + picid" target="_blank">
                ExoFOP
              </a>
            </b-card-text>
          </b-card>
      </b-col>
      <b-col>
        <b-card title="Processing Runs">
          <b-list-group id='observations'>
            <b-list-group-item href="#" v-on:click="selectRow(row)" v-for="row in rows" :class="{'active': row === sourceRunDetail}">
              {{ row.sequence_id }} {{ row.stamp_size }} {{ row.notes }}
            </b-list-group-item>
          </b-list-group>
        </b-card>
      </b-col>
      <b-col>
        <ProcessingDetail
          v-if="sourceRunDetail && piaaRecord"
          v-bind:sourceRunDetail="sourceRunDetail"
          v-bind:piaaRecord="piaaRecord"
        />
      </b-col>
        </div>
    </b-row>
    <b-row>
      <b-col cols="12">
        <div v-if="sourceRunDetail">
          <b-tabs content-class="mt-3">
            <b-tab title="Data">
              <LightcurvePlot
                v-bind:stampData="stampData"
              />
            </b-tab>
            <b-tab title="Raw Flux">
              <RawCountPlot
                v-bind:rawData="rawData"
              />
            </b-tab>
            <b-tab title="Ref Locations" v-if="sourceRunDetail.files.plots">
              <a :href="sourceRunDetail.files.plots['reference-locations']" target="_blank">
                <b-img :src="sourceRunDetail.files.plots['reference-locations']" fluid-grow></b-img>
              </a>
            </b-tab>
            <b-tab title="Ref Distances" v-if="sourceRunDetail.files.plots">
              <a :href="sourceRunDetail.files.plots['reference-pairplot']" target="_blank">
                <b-img :src="sourceRunDetail.files.plots['reference-pairplot']"></b-img>
              </a>
            </b-tab>
            <b-tab title="Coeffs" v-if="sourceRunDetail.files.plots">
              <a :href="sourceRunDetail.files.plots['reference-scores']" target="_blank">
                <b-img :src="sourceRunDetail.files.plots['reference-scores']"></b-img>
              </a>
              <a :href="sourceRunDetail.files.plots['reference-coeffs']" target="_blank">
                <b-img :src="sourceRunDetail.files.plots['reference-coeffs']"></b-img>
              </a>
            </b-tab>
            <b-tab title="Pixel Drift" v-if="sourceRunDetail.files.plots">
              <a :href="sourceRunDetail.files.plots['pixel-drift']" target="_blank">
                <b-img :src="sourceRunDetail.files.plots['pixel-drift']" fluid-grow></b-img>
              </a>
            </b-tab>
            <b-tab title="Ref Vmags" v-if="sourceRunDetail.files.plots">
              <a :href="sourceRunDetail.files.plots['reference-vmags']" target="_blank">
                <b-img :src="sourceRunDetail.files.plots['reference-vmags']">
                </b-img>
              </a>
            </b-tab>
            <b-tab title="Files">
              <ul>
                <li v-for="file in sourceRunDetail.files">
                  <a :href="file">{{ file }}</a>
                </li>
              </ul>
            </b-tab>
          </b-tabs>
        </div>
      </b-col>
    </b-row>
  </b-container>
</template>

<script>
import { SourcesService } from '../services/SourcesService.js'

import LightcurvePlot from './SourceDetail/LightcurvePlot.vue'
import RawCountPlot from './SourceDetail/RawCountPlot.vue'

import ProcessingDetail from './SourceDetail/ProcessingDetail.vue'

const csv = require('csvtojson');
const request = require('request');

let sources = new SourcesService();

export default {
  name: 'SourceDetail',
  components: {
    LightcurvePlot, RawCountPlot,
    ProcessingDetail
  },
  methods: {
    selectRow: function(row) {
      this.sourceRunDetail = row;

      this.sources.getPIAA(this.sourceRunDetail.piaa_document_id)
      .then((piaa_record) => { this.piaaRecord = piaa_record.data(); })
      .catch((err) => { console.log('Error getting PIAA details', err); })
      .finally(() => { this.loading = false; });

      this.sources.getLightcurveData(this.picid, this.sourceRunDetail.id).then((response) => {
        if (response.status == 200){
          this.stampData = response.data.lightcurve;
        }
      }).catch(function(error){
        console.log(error)
      });

      this.sources.getRawCounts(this.picid, this.sourceRunDetail.id).then((response) => {
        if (response.status == 200){
          console.log(response.data.counts);
          this.rawData = response.data.counts;
        }
      });

    },
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
  created () {
    this.sources.getSourceObservations(this.picid).then((observations) => {
        observations.forEach((observation) => {
          var data = observation.data();
          data['id'] = observation.id;
          this.rows.push(data);
        });
      })
      .catch((err) => {
        console.log('Error getting documents', err);
      })
      .finally(() => (this.loading = false));

      this.sources.getSource(this.picid).then((picid_info) => {
        this.sourceRecord = picid_info.data();
      })
      .catch((err) => {
        console.log('Error getting documents', err);
      })
      .finally(() => (this.loading = false));
  },
  data () {
    return {
      rows: [],
      currentStamp: 1,
      stampData: {},
      rawData: {},
      perPage: 1,
      sourceRunDetail: null,
      sourceRecord: null,
      piaaRecord: null,
      sources: sources,
      loading: true,
      picid: this.$route.params.picid
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
