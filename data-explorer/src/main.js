import Vue from 'vue'
import App from './App.vue'
import Buefy from 'buefy'
import 'buefy/dist/buefy.css'
import {firestorePlugin} from 'vuefire'
import router from './router'

Vue.use(firestorePlugin)
Vue.use(Buefy)

Vue.config.productionTip = false

new Vue({
    router,
    render: h => h(App)
}).$mount('#app')
