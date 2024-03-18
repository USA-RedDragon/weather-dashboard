<template>
  <div>
    <Card>
      <template #title>Current Conditions</template>
      <template #content>
      </template>
    </Card>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';

import Card from 'primevue/card';

export default defineComponent({
  name: 'MainPage',
  components: {
    Card,
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
