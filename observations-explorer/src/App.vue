<template>
  <div id="app">
    <router-link to="/"><img id='logo' src="./assets/logo.png"></router-link>
    <h1>{{ name }}</h1>
    <router-view/>
  </div>
</template>

<script>

export default {
  data () {
    return {
      name: 'PANOPTES Observations Explorer'
    }
  }
}
</script>

<style>
#app {
  font-family: 'Fira Code Medium', Helvetica, Arial, sans-serif;
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
h1 a {
  text-decoration: none;
}
</style>
