<template>
  <div id="app">
    <div id="nav">
      <router-link to="/">
        <img id="pan-logo" alt="PANOPTES logo" src="./assets/logo.png">
      </router-link>
    </div>
    <h1>PANOPTES Observations Explorer</h1>
    <router-view/>
  </div>
</template>

<style lang="scss">
#app {
  font-family: 'Avenir', Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
}
#nav {
  padding: .1em;
  a {
    font-weight: bold;
    color: #2c3e50;
    &.router-link-exact-active {
      color: #42b983;
    }
  }
}
#pan-logo {
  height: 3.14159em;
}
h1 {
  font-size: 1.5em;
}
h2 {
  font-size: 1.25em;
}
</style>
