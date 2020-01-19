import Vue from 'vue'

import App from './App.vue'
import router from './router'
import store from './store'
import BootstrapVue from 'bootstrap-vue'
import Buefy from 'buefy'
import { FontAwesomeIcon, FontAwesomeLayers, FontAwesomeLayersText } from '@fortawesome/vue-fontawesome'

import VueGoodTablePlugin from 'vue-good-table'

import 'bootstrap/dist/css/bootstrap.css'
import 'bootstrap-vue/dist/bootstrap-vue.css'
import 'buefy/dist/buefy.css'

import 'vue-good-table/dist/vue-good-table.css'

import axios from 'axios'
import VueAxios from 'vue-axios'
import vuetify from './plugins/vuetify';

Vue.use(BootstrapVue)
Vue.use(Buefy, {
    defaultIconPack: 'fas',
    defaultContainerElement: '#content'
})
Vue.component('font-awesome-icon', FontAwesomeIcon)
Vue.component('font-awesome-layers', FontAwesomeLayers)
Vue.component('font-awesome-layers-text', FontAwesomeLayersText)
Vue.use(VueGoodTablePlugin)
Vue.use(require('vue-moment'))
Vue.use(VueAxios, axios)

Vue.config.productionTip = false

new Vue({
  router,
  store,
  vuetify,
  render: h => h(App)
}).$mount('#app')
