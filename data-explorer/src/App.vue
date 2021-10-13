<template>
  <div id="app">
    <b-navbar>
      <template #start>
        <b-navbar-item tag="router-link" to="/">
          <b-image src="https://avatars.githubusercontent.com/u/5598632?s=400&u=a261881d56cc23ac6b5856efd9d34ef7ed6dd99f&v=4" />
          <h1 class="card-header-title">PANOPTES Data Explorer</h1>
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
