<template>
  <div id="app">
    <img id='logo' src="./assets/logo.png">
    <h1>{{ name }}</h1>
    <router-view/>
  </div>
</template>

<script>

export default {
  name: 'PANOPTES Observations Explorer',
  data () {
    return {
      name: 'PANOPTES Observations Explorer'
    }
  }
}
</script>

<style>
#app {
  font-family: 'Avenir', Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  margin-top: 60px;
}
#logo {
  width: 20em;
  margin-top: -3em;
  margin-bottom: 1em;
}
h1 {
  font-size: 1.5em;
}
</style>
