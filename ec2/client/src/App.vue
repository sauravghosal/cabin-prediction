<template>
  <home-vue />
</template>

<script>
import HomeVue from "./pages/Home.vue";
export default {
  name: "App",
  components: {
    HomeVue,
  },
};
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
}
body {
  margin: 0 !important;
}
</style>
