<template>
  <b-navbar>
    <template #brand>
      <b-navbar-item tag="a" href="/">
        <img
            src="https://avatars.githubusercontent.com/u/5598632?s=400&u=a261881d56cc23ac6b5856efd9d34ef7ed6dd99f&v=4"
            :alt="name"
        >
        <h1 class="card-header-title">{{ name }}</h1>
      </b-navbar-item>
    </template>
  </b-navbar>
</template>


<script>
export default {
  data() {
    return {
      name: 'PANOPTES Data Explorer'
    }
  }
}
</script>

<style scoped>

</style>
