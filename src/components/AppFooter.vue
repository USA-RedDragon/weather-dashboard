<template>
  <div class="footer">
    <p>
      This project is proudly open
      <a href="https://github.com/USA-RedDragon/weather-dashboard" target="_blank"
        >source</a
      >
    </p>
    <p>Copyright &copy; 2024-{{ year }} Jacob McSwain</p>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';

export default defineComponent({
  data: function() {
    return {
      year: new Date().getFullYear(),
    };
  },
  // Get version from API onMounted
  mounted() {},
});
</script>

<style scoped>
.footer {
  text-align: center;
  display: block;
  padding: 1em;
  padding-bottom: 0;
  margin-bottom: 0;
  font-size: 0.8em;
}
</style>
