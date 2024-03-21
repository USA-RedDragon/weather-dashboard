<template>
  <div>
    <canvas id="radarCanvas"></canvas>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import * as d3 from 'd3';

import * as radar from '../services/radar';
import type radarScan from '../services/radar';

type data = {
  context: CanvasRenderingContext2D | null;
  currentTimestamp: Date | string;
  scannerCancel: (() => void) | null;
  canvas: d3.Selection<d3.BaseType, unknown, HTMLElement, any> | null;
}

export default defineComponent({
  props: {
    sweep: {
      type: Number,
      default: 0,
    },
    projection: {
      type: Function,
      default: (val: any) => val,
    },
    width: {
      type: Number,
      default: 0,
    },
    height: {
      type: Number,
      default: 0,
    },
  },
  emits: ['timestamp'],
  data: function(): data {
    return {
      context: null,
      currentTimestamp: 'Loading...',
      scannerCancel: null,
      canvas: null,
    };
  },
  unmounted() {
    if (this.scannerCancel) {
      this.scannerCancel();
    }
  },
  mounted() {
    this.canvas = d3.select('#radarCanvas')
      .attr('height', `${this.height}`)
      .attr('width', `${this.width}`);
    if (!this.canvas) {
      console.error('Failed to get canvas');
      return;
    }
    const node = this.canvas.node() as HTMLCanvasElement;
    if (!node) {
      console.error('Failed to get canvas node');
      return;
    }
    this.context = node.getContext('2d');
    this.draw();
  },
  watch: {
    sweep: function() {
      this.$emit('timestamp', 'Loading...');
      this.draw();
    },
    projection: function() {
      this.$emit('timestamp', 'Adjusting...');
      this.draw();
    },
    width: function() {
      this.$emit('timestamp', 'Adjusting...');
      this.canvas?.attr('width', `${this.width}`);
      this.draw();
    },
    height: function() {
      this.$emit('timestamp', 'Adjusting...');
      this.canvas?.attr('height', `${this.height}`);
      this.draw();
    },
  },
  methods: {
    async draw(scan: radarScan | null = null): Promise<void> {
      this.context?.clearRect(0, 0, this.width, this.height);
      let radarPromise = new Promise<radarScan>((resolve) => {
        resolve(scan);
      });
      if (!scan) {
        radarPromise = radar.getScan('ktlx', this.sweep);
      }
      const radarData = await radarPromise;
      this.currentTimestamp = new Date(radarData.timestamp * 1000);
      this.$emit('timestamp', this.currentTimestamp);
      this.drawRadar(radarData);

      if (this.scannerCancel) {
        this.scannerCancel();
      }
      if (!this.scannerCancel) {
        const ts = (this.currentTimestamp as unknown) as number;
        this.scannerCancel = radar.listenForNewScan('ktlx', this.sweep, ts, (scan: radarScan) => {
          this.$emit('timestamp', 'Loading...');
          this.draw(scan);
        });
      }
    },
    drawRadar(data: radarScan) {
      if (!this.context) {
        console.error('context is null');
        return;
      }

      // xlocs and ylocs are 2-dimensional arrays where:
      // - (X[i, j], Y[i, j]) is the bottom left of the polgon
      // - (X[i, j + 1], Y[i, j + 1]) is the bottom right of the polygon
      // - (X[i + 1, j], Y[i + 1, j]) is the top left of the polygon
      // - (X[i + 1, j + 1], Y[i + 1, j + 1]) is the top right of the polygon
      //
      // X = [
      //   [10, 20],
      // ]
      // Y = [
      //   [40, 50],
      // ]
      // This results in the following quadrilateral polygon:
      // - (10, 40) bottom left
      // - (20, 40) bottom right
      // - (10, 50) top left
      // - (20, 50) top right

      // data is a 2-dimensional array where the index corresponds to the polygon at the same index in xlocs and ylocs
      //
      // data = [
      //   [0.5],
      // ]
      // This results in the following:
      // - The polygon at (0, 1) has a value of 0.5

      for (let i = 0; i < data.xlocs.length-1; i++) {
        for (let j = 0; j < data.ylocs.length-1; j++) {
          const bottomLeft = this.projection([data.xlocs[i][j], data.ylocs[i][j]]);
          const bottomRight = this.projection([data.xlocs[i][j + 1], data.ylocs[i][j + 1]]);
          const topLeft = this.projection([data.xlocs[i + 1][j], data.ylocs[i + 1][j]]);
          const topRight = this.projection([data.xlocs[i + 1][j + 1], data.ylocs[i + 1][j + 1]]);
          const value = data.data[i][j];

          if (value) {
            this.context.beginPath();
            this.context.moveTo(bottomLeft[0], bottomLeft[1]);
            this.context.lineTo(bottomRight[0], bottomRight[1]);
            this.context.lineTo(topRight[0], topRight[1]);
            this.context.lineTo(topLeft[0], topLeft[1]);
            this.context.lineTo(bottomLeft[0], bottomLeft[1]);
            this.context.fillStyle = radar.colormap(value);
            this.context.fill();
          }
        }
      }
    },
  },
});
</script>

<style scoped>
#radarCanvas {
  z-index: 100;
  height: 100%;
  width: 100%
}
</style>
