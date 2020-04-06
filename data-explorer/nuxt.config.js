import colors from 'vuetify/es5/util/colors'

export default {
  mode: 'spa',
  // server: {
  //   port: 3000, // default: 3000
  //   host: '0.0.0.0' // default: localhost
  // },
  /*
  ** Headers of the page
  */
  head: {
    titleTemplate: '%s - ' + process.env.npm_package_name,
    title: process.env.npm_package_name || '',
    meta: [
      { charset: 'utf-8' },
      { name: 'viewport', content: 'width=device-width, initial-scale=1' },
      { hid: 'description', name: 'description', content: process.env.npm_package_description || '' }
    ],
    script: [
      { src: 'http://localhost:5000/__/firebase/7.7.0/firebase-app.js' },
      { src: 'http://localhost:5000/__/firebase/7.7.0/firebase-auth.js' },
      { src: 'http://localhost:5000/__/firebase/7.7.0/firebase-storage.js' },
      { src: 'http://localhost:5000/__/firebase/7.7.0/firebase-firestore.js' },
      { src: 'http://localhost:5000/__/firebase/7.7.0/firebase-functions.js' },
      { src: 'http://localhost:5000/__/firebase/init.js' }
    ],
    link: [
      { rel: 'icon', type: 'image/x-icon', href: '/favicon.ico' }
    ]
  },
  /*
  ** Customize the progress-bar color
  */
  loading: { color: '#fff' },
  /*
  ** Global CSS
  */
  css: [
  ],
  /*
  ** Plugins to load before mounting the App
  */
  plugins: [
    '~/plugins/firebase.js',
    '~/plugins/moment.js'
    ],
  /*
  ** Nuxt.js dev-modules
  */
  buildModules: [
    '@nuxtjs/vuetify',
  ],
  /*
  ** Nuxt.js modules
  */
  modules: [
    // Doc: https://axios.nuxtjs.org/usage
    '@nuxtjs/axios',
    // Doc: https://github.com/nuxt-community/dotenv-module
    '@nuxtjs/dotenv',
  ],
  /*
  ** Axios module configuration
  ** See https://axios.nuxtjs.org/options
  */
  axios: {
  },
  /*
  ** vuetify module configuration
  ** https://github.com/nuxt-community/vuetify-module
  */
  vuetify: {
    customVariables: ['~/assets/variables.scss'],
    theme: {
      light: true,
      dark: false,
      themes: {
        light: {
          primary: '#607d8b',
          secondary: '#009688',
          accent: '#3f51b5',
          error: '#e91e63',
          warning: '#ffc107',
          info: '#03a9f4',
          success: '#2196f3'
        }
      }
    }
  },
  /*
  ** Build configuration
  */
  build: {
    /*
    ** You can extend webpack config here
    */
    extend (config, ctx) {
    }
  }
}
