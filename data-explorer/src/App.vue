<template>
  <div id="app">
    <Header />
    <RecentImages />
  </div>
</template>

<script>
import Header from "./components/Header";
import RecentImages from './components/RecentImages.vue'

export default {
  name: 'App',
  components: {
    Header,
    RecentImages
  }
}
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  margin-top: 60px;
}
</style>
