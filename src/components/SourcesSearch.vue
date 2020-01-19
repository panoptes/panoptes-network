<template>
  <section>
    <form v-on:submit.prevent="submitForm">
        <div class="modal-card" style="width: auto">
            <header class="modal-card-head">
                <p class="modal-card-title">
                Search the stars</p>
            </header>
            <section class="modal-card-body">
                <b-field horizontal label="RA [deg]">
                    <b-input
                        v-model.number="searchModel.ra"
                        placeholder="300.01">
                    </b-input>
                    <b-input
                      v-model.number="searchModel.raRadius"
                      placeholder="Radius"
                      ></b-input>
                    <b-select v-model="searchModel.radiusUnits">
                        <option>Degree</option>
                        <option>Arcmin</option>
                        <option>Arcsec</option>
                    </b-select>
                </b-field>
                <b-field horizontal label="Dec [deg]">
                    <b-input
                        v-model.number="searchModel.dec"
                        placeholder="70.01">
                    </b-input>
                    <b-input
                      v-model.number="searchModel.decRadius"
                      placeholder="Radius"
                      ></b-input>
                    <b-select v-model="searchModel.radiusUnits" disabled>
                        <option>Degree</option>
                        <option>Arcmin</option>
                        <option>Arcsec</option>
                    </b-select>
                </b-field>

                <b-field horizontal label="Vmag range">
                    <b-slider v-model="searchModel.vmagRange" :min="6" :max="12" :step="0.5" ticks>
                      <template v-for="val in [6,8,10,12]">
                        <b-slider-tick :value="val">{{ val }}</b-slider-tick>
                      </template>
                    </b-slider>
                </b-field>
            </section>
            <footer class="modal-card-foot">
                <button class="button" type="button" @click="submitForm">Close</button>
                <button class="button is-primary">Search</button>
            </footer>
        </div>
    </form>
  </section>
</template>

<script>
import { mapState } from 'vuex'

export default {
  name: 'SourcesSearch',
  components: {},
  methods: {
    submitForm: function() {
      // Fetch the results
      this.$store.dispatch('searchSources');
      this.$parent.close();
    }
  },
  computed: {
    ...mapState(['searchModel'])
  },
  data () {
    return {
    }
  }
}
</script>
