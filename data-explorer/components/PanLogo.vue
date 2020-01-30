<template>
  <img
    class="PanLogo"
    alt="PANOPTES Logo"
    src="https://projectpanoptes.org/uploads/2018/12/17/pan-head.png"
  />
</template>

<style>
.PanLogo {
  width: 180px;
  transform: rotateY(560deg);
  animation: turn 3.5s ease-out forwards 1s;
}

@keyframes turn {
  100% {
    transform: rotateY(0deg);
  }
}
</style>
