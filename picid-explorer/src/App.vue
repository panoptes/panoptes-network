<template>
  <b-container fluid id="app">
    <b-navbar>
      <template slot="brand">
        <b-navbar-item tag="router-link" :to="{ path: '/' }">
          <img id="pan-logo" alt="PANOPTES logo" src="./assets/logo.png">
        </b-navbar-item>
      </template>
      <template slot="start">
        <b-navbar-item href="/observations">
            Observations
        </b-navbar-item>
        <b-navbar-item href="/piaa">
            Stars
        </b-navbar-item>
      </template>
    </b-navbar>
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
}
#nav {
  text-align: center;
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
