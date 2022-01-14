<template>
  <div id="app">
    <b-navbar>
      <template #start>
        <b-navbar-item tag="router-link" to="/">
          <h1 class="title is-3">PANOPTES Data Explorer</h1>
        </b-navbar-item>
      </template>
    </b-navbar>
    <router-view/>
  </div>
</template>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
}

#nav {
  padding: 30px;
}

#nav a {
  font-weight: bold;
  color: #2c3e50;
}

#nav a.router-link-exact-active {
  color: #42b983;
}
</style>
