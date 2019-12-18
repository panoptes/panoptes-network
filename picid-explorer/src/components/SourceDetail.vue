<template>
  <b-container class="observations">
    <b-row> <a href="/piaa">PICID List</a> </b-row>
    <b-row>
      <b-col cols="4">
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
        <b-card title="Processing Runs">
          <b-list-group id='observations'>
            <b-list-group-item href="#" v-on:click="selectRow(row)" v-for="row in rows" :class="{'active': row === sourceRunDetail}">
              {{ row.sequence_id }} {{ row.stamp_size }} {{ row.notes }}
            </b-list-group-item>
          </b-list-group>
        </b-card>
        <div>
          <b-card v-if="sourceRunDetail" title="Processing Details">
            <b-card-text>
              <dl class="row">
                <dt class="col-sm-5">Notes:</dt>
                <dd class="col-sm-7">{{ sourceRunDetail.notes }}</dd>
                <dt class="col-sm-5">Stamp Size:</dt>
                <dd class="col-sm-7">{{ piaaRecord.stamp_size}}</dd>
                <dt class="col-sm-5">Num refs:</dt>
                <dd class="col-sm-7">{{ sourceRunDetail.num_refs }}</dd>
                <dt class="col-sm-5">Sequence ID:</dt>
                <dd class="col-sm-7">
                  <a :href="'/observations/' + sourceRunDetail.sequence_id" target="_blank">{{ sourceRunDetail.sequence_id }}</a>
                </dd>
                <dt class="col-sm-5">Run ID:</dt>
                <dd class="col-sm-7">{{ sourceRunDetail.piaa_document_id }}</dd>
              </dl>
            </b-card-text>
          </b-card>
        </div>
      </b-col>
      <b-col cols="8">
        <div v-if="sourceRunDetail">
          <b-tabs content-class="mt-3">
            <b-tab title="Data">
              <Plotly
                :data="stampData"
                :layout="layout"
              /></Plotly>
            </b-tab>
            <b-tab title="Lightcurve" v-if="sourceRunDetail.files.plots">
              <a :href="sourceRunDetail.files.plots['lightcurve-plot']" target="_blank">
                <b-img :src="sourceRunDetail.files.plots['lightcurve-plot']" fluid-grow></b-img>
              </a>
            </b-tab>
            <b-tab title="Lightcurve Clipped" v-if="sourceRunDetail.files.plots">
              <a :href="sourceRunDetail.files.plots['lightcurve-plot-clipped']" target="_blank">
                <b-img :src="sourceRunDetail.files.plots['lightcurve-plot-clipped']" fluid-grow></b-img>
              </a>
            </b-tab>
            <b-tab title="Raw Flux 01" v-if="sourceRunDetail.files.plots">
              <a :href="sourceRunDetail.files.plots['raw-flux-01']" target="_blank">
                <b-img :src="sourceRunDetail.files.plots['raw-flux-01']" fluid-grow></b-img>
              </a>
            </b-tab>
            <b-tab title="Raw Flux 02" v-if="sourceRunDetail.files.plots">
              <a :href="sourceRunDetail.files.plots['raw-flux-02']" target="_blank">
                <b-img :src="sourceRunDetail.files.plots['raw-flux-02']" fluid-grow></b-img>
              </a>
            </b-tab>`
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
import { Plotly } from 'vue-plotly'

const csv = require('csvtojson');
const request = require('request');

let sources = new SourcesService();

export default {
  name: 'SourceDetail',
  components: {
    Plotly
  },
  methods: {
    selectRow: function(row) {
      this.sourceRunDetail = row;

      this.sources.getPIAA(this.sourceRunDetail.piaa_document_id)
      .then((piaa_record) => { this.piaaRecord = piaa_record.data(); })
      .catch((err) => { console.log('Error getting PIAA details', err); })
      .finally(() => { this.loading = false; });

      // Get lightcurve data
      var image_times = [];
      var r_data = [];
      var g_data = [];
      var b_data = [];

      csv()
      .fromStream(request.get(this.sourceRunDetail.files['lightcurve-data']))
      .subscribe((json)=>{
          image_times.push(json.image_time);
          r_data.push(json.r);
          g_data.push(json.g);
          b_data.push(json.b);
      });

      this.stampData = [
        {
          x: image_times,
          y: r_data,
          mode: 'lines+markers',
          name: 'R data',
          line: {
            color: 'red',
            size: 3
          },
          marker: {
            color: 'red',
            size: 7
          }
        },
        {
          x: image_times,
          y: g_data,
          mode: 'lines+markers',
          name: 'G data',
          line: {
            color: 'green',
            size: 3
          },
          marker: {
            color: 'green',
            size: 7
          }
        },
        {
          x: image_times,
          y: b_data,
          mode: 'lines+markers',
          name: 'B data',
          line: {
            color: 'blue',
            size: 3
          },
          marker: {
            color: 'blue',
            size: 7
          }
        },
      ];

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
      stampData: [],
      perPage: 1,
      sourceRunDetail: null,
      sourceRecord: null,
      piaaRecord: null,
      sources: sources,
      loading: true,
      picid: this.$route.params.picid,
      layout: {
        title: 'Lightcurve ' + this.$route.params.picid,
        colors: ['red', 'green', 'blue']
      }
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
.list-group {
  max-height: 300px;
  margin-bottom: 10px;
  overflow: scroll;
  -webkit-overflow-scrolling: touch;
}
</style>
