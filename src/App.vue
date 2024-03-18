<template>
  <AppHeader />
  <RouterView />
  <AppFooter />
  <ThemeConfig />
</template>

<script lang="ts">
import { RouterView } from 'vue-router';
import AppFooter from './components/AppFooter.vue';
import AppHeader from './components/AppHeader.vue';
import ThemeConfig from './components/ThemeConfig.vue';

import { mapStores } from 'pinia';
import { useSettingsStore } from './store';
import { defineComponent } from 'vue';

export default defineComponent({
  name: 'App',
  components: {
    RouterView,
    AppHeader,
    AppFooter,
    ThemeConfig,
  },
  data() {
    return {};
  },
  watch: {},
  created() {},
  mounted() {},
  unmounted() {},
  methods: {},
  computed: {
    ...mapStores(useSettingsStore),
  },
});
</script>

<style scoped></style>
