<template>
  <b-container fluid id="app">
    <div id="nav">
      <router-link to="/">
        <img id="pan-logo" alt="PANOPTES logo" src="./assets/logo.png">
      </router-link>
    </div>
    <h1 class="subtitle">PANOPTES Observations Explorer</h1>
    <b-row id="content">
      <b-col cols="12">
        <router-view id="routerView"/>
      </b-col>
    </b-row>
  </b-container>
</template>

<style lang="scss">
#app {
  font-family: 'Avenir', Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
}
#nav {
  margin-top: 1em;
}
#routerView .container
 {
  max-width: 98%;
}
#pan-logo {
  height: 3.14159em;
}
</style>
