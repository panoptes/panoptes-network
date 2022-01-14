<template>
  <div class="tile is-ancestor">
    <div class="tile is-12 is-vertical is-parent">
      <div class="tile is-child box">
        <p class="title">Images</p>
        <RecentImages/>
      </div>
      <div class="tile is-child box">
        <p class="title">Observations</p>
        <Observations/>
      </div>
    </div>
  </div>
</template>

<script>
import RecentImages from "@/components/RecentImages";
import Observations from "@/components/Observations";

export default {
  name: 'Home',
  components: {
    RecentImages,
    Observations
  }
}
</script>
