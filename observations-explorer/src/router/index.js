import Vue from 'vue'
import Router from 'vue-router'
import Observations from '@/components/Observations'
import ObservationDetail from '@/components/ObservationDetail'

Vue.use(Router)

export default new Router({
  routes: [
    {
      path: '/',
      name: 'Observations',
      component: Observations
    },
    {
      path: '/observations/:id',
      name: 'Observation Detail',
      component: ObservationDetail
    }
  ]
})
