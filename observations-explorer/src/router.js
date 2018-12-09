import Vue from 'vue'
import Router from 'vue-router'
import Observations from './views/Observations.vue'

Vue.use(Router)

export default new Router({
  mode: 'history',
  base: process.env.BASE_URL,
  routes: [
    {
      path: '/',
      name: 'home',
      component: Observations
    },
    {
      path: '/observations/:sequenceId',
      name: 'observationDetail',
      // route level code-splitting
      // this generates a separate chunk (about.[hash].js) for this route
      // which is lazy-loaded when the route is visited.
      component: () => import(/* webpackChunkName: "about" */ './views/ObservationDetail.vue')
    },
    { path: '*', redirect: 'home' }
  ]
})
