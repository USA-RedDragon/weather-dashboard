<template>
  <div>
    <Card>
      <template #title>Current Conditions</template>
      <template #content>
        <MapChart country :data="[]" :options="{}" />
      </template>
    </Card>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';

import Card from 'primevue/card';
import MapChart from '../components/MapChart.vue';

export default defineComponent({
  name: 'MainPage',
  components: {
    Card,
    MapChart,
  },
  data() {
    return {};
  },
  watch: {},
  created() {},
  mounted() {},
  unmounted() {},
  methods: {},
  computed: {},
});
</script>
