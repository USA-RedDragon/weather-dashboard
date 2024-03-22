<template>
  <div id="canvasWrapper">
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import * as PIXI from 'pixi.js';

import * as radar from '../services/radar';

type data = {
  currentTimestamp: Date | string;
  scannerCancel: (() => void) | null;
  app: PIXI.Application | null;
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
      currentTimestamp: 'Loading...',
      scannerCancel: null,
      app: null,
    };
  },
  unmounted() {
    if (this.scannerCancel) {
      this.scannerCancel();
    }
  },
  mounted() {
    const canvas = document.createElement('canvas');
    canvas.id = 'radarCanvas';
    document.getElementById('canvasWrapper')?.appendChild(canvas);
    const view = canvas.transferControlToOffscreen();
    this.app = new PIXI.Application({
      backgroundAlpha: 0,
      antialias: true,
      width: this.width,
      height: this.height,
      view: (view as any),
    });
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
      // this.canvas?.attr('width', `${this.width}`);
      this.draw();
    },
    height: function() {
      this.$emit('timestamp', 'Adjusting...');
      // this.canvas?.attr('height', `${this.height}`);
      this.draw();
    },
  },
  methods: {
    async draw(scan: radarScan | null = null): Promise<void> {
      while (window['pyodide'] === undefined) {
        await new Promise((resolve) => setTimeout(resolve, 100));
      }
      let radarPromise = new Promise<radarScan | null>((resolve) => {
        resolve(scan);
      });
      if (!scan) {
        radarPromise = radar.getScan('ktlx', this.sweep);
      }
      const radarData = await radarPromise;
      if (!radarData) {
        return;
      }
      this.currentTimestamp = new Date(radarData.timestamp * 1000);
      this.app!.stage.removeChildren();

      const [xlocs, ylocs] = (window.pyodide.azimuthRangeToLatLon(
        radarData.az,
        radarData.ref_range,
        radarData.cent_lon,
        radarData.cent_lat,
      ).toJs() as [number[][], number[][]]);

      this.drawRadar(xlocs, ylocs, radarData.data);
      this.$emit('timestamp', this.currentTimestamp);

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
    drawRadar(xlocs: number[][], ylocs: number[][], data: number[][]): void {
      if (!this.app) {
        console.error('app is null');
        return;
      }

      const graphics = new PIXI.Graphics();
      for (let i = 0; i < xlocs.length-1; i++) {
        for (let j = 0; j < ylocs.length-1; j++) {
          const bottomLeft = this.projection([xlocs[i][j], ylocs[i][j]]);
          const bottomRight = this.projection([xlocs[i][j + 1], ylocs[i][j + 1]]);
          const topLeft = this.projection([xlocs[i + 1][j], ylocs[i + 1][j]]);
          const topRight = this.projection([xlocs[i + 1][j + 1], ylocs[i + 1][j + 1]]);
          const value = data[i][j];

          if (value) {
            graphics.lineStyle(0)
              .beginFill(radar.colormap(value), 0.75)
              .moveTo(bottomLeft[0], bottomLeft[1])
              .lineTo(bottomRight[0], bottomRight[1])
              .lineTo(topRight[0], topRight[1])
              .lineTo(topLeft[0], topLeft[1])
              .lineTo(bottomLeft[0], bottomLeft[1])
              .endFill();
          }
        }
      }
      this.app.stage.addChild(graphics);
    },
  },
});
</script>

<style scoped>
#radarCanvas {
  z-index: 100;
  height: 100%;
  width: 100%;
}
</style>
