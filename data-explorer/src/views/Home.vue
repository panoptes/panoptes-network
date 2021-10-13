<template>
  <div class="home">
    <RecentImages />
    <Observations />
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
