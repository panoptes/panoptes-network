<template>
  <v-container>
    <v-dialog
      v-model="modalActive"
      width="500"
    >
      <template v-slot:activator="{ on }">
        <v-row no-gutters>
          <v-col
            cols="12"
            sm="8"
          >
            <v-text-field
              disabled
              flat
              solo-inverted
              hide-details
              prepend-inner-icon="mdi-magnify"
              :label="searchLabel"
              class="hidden-sm-and-down"
            />
          </v-col>
          <v-col
            cols="12"
            sm="4"
            >
              <v-btn
                class="ma-2"
                color="primary"
                dark
                v-on="on"
              >
                <v-icon dark left>mdi-table-search</v-icon> Search
              </v-btn>
          </v-col>
        </v-row>
      </template>

      <v-card>
        <v-card-title
          class="headline primary dark white--text"
          primary-title
        >
          <v-toolbar-title>
            <v-row no-gutters>
              <v-col cols="3" class="text-left">
                <v-icon color="white">mdi-star</v-icon>
              </v-col>

              <v-col cols="6" class="text-center">
                Search the stars...
              </v-col>

              <v-col cols="3" class="text-right">
                <v-icon color="white">mdi-star</v-icon>
              </v-col>
            </v-row>
          </v-toolbar-title>
        </v-card-title>

        <v-card-text>
          <v-form
            ref="form"
            v-model="searchModel.valid"
            lazy-validation
          >
            <v-row>
              <v-col >
                <v-text-field
                  v-model="searchModel.searchString"
                  label="Target name"
                  :disabled="haveCoords"
                  placeholder="Enter name of target"
                  >
                    <v-btn
                      slot="append"
                      @click="lookupField"
                      v-on="on"
                      > <v-icon>mdi-magnify</v-icon>
                      </v-btn>
                  </v-text-field>
                </v-col>
            </v-row>
            <v-divider></v-divider>
            <v-row>
              <v-col>
                <v-text-field
                  v-model="searchModel.ra"
                  :rules="raRules"
                  label="RA"
                  required
                  ></v-text-field>
              </v-col>
              <v-col>
                <v-text-field
                  v-model="searchModel.dec"
                  :rules="decRules"
                  label="Dec"
                  required
                  ></v-text-field>
              </v-col>
              <v-col>
                <v-text-field
                  v-model="searchModel.searchRadius"
                  label="Radius"
                  :rules="radiusRules"
                  required
                  ></v-text-field>
              </v-col>
              <v-col>
                <v-select
                  :items="searchModel.radiusUnits"
                  value='Degree'
                  label="Units"
                ></v-select>
              </v-col>
            </v-row>
            <v-row>
              <v-col>
                <v-range-slider
                  label="Vmag Range"
                  v-model="searchModel.vmagRange"
                  :max="13"
                  :min="6"
                  ticks="always"
                  :step="0.5"
                  :tickLabels="[6,,7,,8,,9,,10,,11,,12,,13]"
                >
                </v-range-slider>
              </v-col>
            </v-row>
            <v-row>
              <v-col>
                <v-combobox
                  v-model="selectedUnits"
                  disabled
                  :items="units"
                  label="PANOPTES Units"
                  item-key="unit_id"
                  item-text="unit_id"
                  :return-object="true"
                  multiple
                  chips
                ></v-combobox>
              </v-col>
            </v-row>
            <v-row>
              <v-col>
                <v-menu
                  ref="menu"
                  v-model="startPickerMenu"
                  :close-on-content-click="true"
                  :return-value.sync="searchModel.startDate"
                  transition="scale-transition"
                  offset-y
                  min-width="290px"
                >
                  <template v-slot:activator="{ on }">
                    <v-text-field
                      disabled
                      v-model="searchModel.startDate"
                      label="Start Date"
                      prepend-icon="mdi-calendar"
                      readonly
                      v-on="on"
                    ></v-text-field>
                  </template>
                  <v-date-picker v-model="searchModel.startDate" no-title scrollable>
                    <v-spacer></v-spacer>
                    <v-btn text color="primary" @click="menu = false">Cancel</v-btn>
                    <v-btn text color="primary" @click="$refs.menu.save(searchModel.startDate)">OK</v-btn>
                  </v-date-picker>
                </v-menu>
              </v-col>
              <v-col>
                <v-menu
                  ref="menu"
                  v-model="endPickerMenu"
                  :close-on-content-click="true"
                  :return-value.sync="searchModel.endDate"
                  transition="scale-transition"
                  offset-y
                  min-width="290px"
                >
                  <template v-slot:activator="{ on }">
                    <v-text-field
                      v-model="searchModel.endDate"
                      disabled
                      label="End Date"
                      prepend-icon="mdi-calendar"
                      readonly
                      v-on="on"
                    ></v-text-field>
                  </template>
                  <v-date-picker v-model="searchModel.endDate" no-title scrollable>
                    <v-spacer></v-spacer>
                    <v-btn text color="primary" @click="menu = false">Cancel</v-btn>
                    <v-btn text color="primary" @click="$refs.menu.save(searchModel.endDate)">OK</v-btn>
                  </v-date-picker>
                </v-menu>
              </v-col>
            </v-row>

          </v-form>
        </v-card-text>

        <v-divider></v-divider>

        <v-card-actions>
            <v-btn color="error" @click="reset"> Reset </v-btn>
            <v-spacer></v-spacer>
            <v-btn
              :disabled="!searchModel.valid"
              color="primary"
              @click="validate"
            >
              Search
            </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script>
import { mapState } from 'vuex'

export default {
  name: 'SourcesSearch',
  components: {},
  computed: {
    ...mapState([
      'units',
      'searchModel',
      'isSearching',
      'fromSearch'
    ]),
    searchLabel: function() {
      if (this.fromSearch) {
        let label = 'RA= ' + this.searchModel.ra + '° Dec= ' + this.searchModel.dec + '°';
        label += ' Radius= ' + this.searchModel.searchRadius + '°';
        return label;
      } else {
        return 'Enter PICID, Observation ID, Image ID, RA/Dec, etc.';
      }
    },
  },
  watch: {
    modalActive: function(val) {
      this.$store.commit('toggleSearchForm');
    },
    isSearching: function(val) {
      this.haveCoords = val;
    },
  },
  mounted: function () {
    this.$nextTick(function () {
      this.$store.dispatch('getUnits');
    })
  },
  methods: {
    submitForm: function() {
      // Fetch the results
      this.$store.dispatch('searchObservations');
      this.$store.dispatch('searchSources');
      this.modalActive = false;
    },
    lookupField: function() {
      this.$store.dispatch('lookupField');
    },
    validate () {
      if (this.$refs.form.validate()) {
        this.submitForm();
      }
    },
    reset () {
      this.$refs.form.reset();
    },
    resetValidation () {
      this.$refs.form.resetValidation()
    },
  },
  data: () => ({
    search: null,
    selectedUnits: [],
    startPickerMenu: false,
    endPickerMenu: false,
    modalActive: false,
    haveCoords: false,
    on: false,
    raRules: [
        v => v <= 360 || 'RA must be less than 360°',
        v => v >= -360 || 'RA must be greater than -360°',
    ],
    decRules: [
        v => v <= 180 || 'Dec must be less than 180°',
        v => v >= -180 || 'Dec must be greater than -180°',
    ],
    radiusRules: [
        v => v >= 0 || 'Search radius must be greater than 0',
    ],
  }),
}
</script>
