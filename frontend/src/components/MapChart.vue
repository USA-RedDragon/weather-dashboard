<template>
  <div>
    <div v-if="radar">
      <p>Radar Scan: <span v-if="!loading">{{currentTimestamp.toString()}}</span><span v-else>Loading...</span></p>
      <br />
      <p>Sweep Angle</p>
      <!-- @vue-expect-error PrimeVue doesn't have the proper
          type, only Nullable<string>, but passing a string
          value breaks the component -->
      <InputNumber :disabled="loading" v-model.number="sweep" :max="7" :min="0" class="w-14rem"></InputNumber>
      <Slider @change="loading = true" :disabled="loading" v-model="sweep" :step="1" :max="7" class="w-14rem"></Slider>
      <br />
    </div>
    <div class="layered">
      <canvas></canvas>
      <RadarCanvas
        v-if="radar"
        @timestamp="updateTimestamp"
        @loading="loading = $event.value ; $nextTick($event.callback)"
        :loading="loading"
        :projection="projection"
        :sweep="sweep"
        :width="width"
        :height="height" />
    </div>
  </div>
</template>

<script lang="ts">
/// <reference path="../services/alerts.d.ts" />
import { defineComponent } from 'vue';
import axios from 'axios';
import * as d3 from 'd3';
import InputNumber from 'primevue/inputnumber';
import Slider from 'primevue/slider';
import { getGeoJSON } from '../services/geojson';
import RadarCanvas from './RadarCanvas.vue';

type data = {
  height: number;
  width: number;
  sweep: number;
  loading: boolean;
  currentTimestamp: Date;
  projection: d3.GeoProjection;
  geoGenerator: d3.GeoPath | null;
  canvas: d3.Selection<d3.BaseType, unknown, HTMLElement, any> | null;
  context: CanvasRenderingContext2D | null;
  alerts: WXAlert[];
}

type drawGeoJSONOptions = {
  stroke: string,
  fill: string,
  strokeWidth: string,
  data: any,
}

export default defineComponent({
  components: {
    InputNumber,
    Slider,
    RadarCanvas,
  },
  props: {
    data: {
      type: Object,
      required: true,
    },
    options: {
      type: Object,
      required: true,
    },
    country: {
      type: Boolean,
      required: false,
      default: false,
    },
    state: {
      type: String,
      required: false,
      default: '',
    },
    radar: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  data: (): data => {
    return {
      height: 1080,
      width: 1920,
      sweep: 0,
      loading: true,
      projection: d3.geoEquirectangular(),
      geoGenerator: null,
      currentTimestamp: new Date(0),
      canvas: null,
      context: null,
      alerts: [],
    };
  },
  mounted() {
    axios.get('/api/alerts/ok').then((response) => {
      this.alerts = response.data as WXAlert[];
      this.draw();
    });
    this.canvas = d3.select('canvas')
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
  methods: {
    async draw() {
      this.context?.clearRect(0, 0, this.width, this.height);
      if (this.country) {
        await this.drawCountry();
      } else if (this.state) {
        await this.drawState();
      }
    },
    drawAlerts() {
      for (let i=0; i<this.alerts.length; i++) {
        const alert = this.alerts[i];
        if (!alert.geometry) {
          continue;
        }
        console.log(this.hexToRGB(alert.color, 1));

        this.drawGeoJSON({
          stroke: alert.is_weather ? this.hexToRGB(alert.color, 1):'rgba(0, 0, 0, 1)',
          strokeWidth: '1',
          fill: alert.is_weather ? 'rgba(0, 0, 0, 0)':this.hexToRGB(alert.color, 1),
          data: alert.geometry,
        });
      }
    },
    hexToRGB(hex: string, alpha: number) {
      const r = parseInt(hex.slice(1, 3), 16);
      const g = parseInt(hex.slice(3, 5), 16);
      const b = parseInt(hex.slice(5, 7), 16);

      if (alpha) {
        return 'rgba(' + r + ', ' + g + ', ' + b + ', ' + alpha + ')';
      } else {
        return 'rgb(' + r + ', ' + g + ', ' + b + ')';
      }
    },
    updateTimestamp(ts: Date) {
      this.currentTimestamp = ts;
    },
    drawGeoJSON(options: drawGeoJSONOptions) {
      if (!this.geoGenerator) {
        console.error('geoGenerator is null');
        return;
      }
      if (!this.context) {
        console.error('context is null');
        return;
      }
      this.context.save();

      this.context.strokeStyle = options.stroke;
      this.context.fillStyle = options.fill;
      this.context.lineWidth = parseFloat(options.strokeWidth);

      this.context.beginPath();
      this.geoGenerator(options.data);
      this.context.stroke();
      this.context.fill();

      this.context.restore();
    },
    drawCountry(): Promise<void> {
      // Center and zoom on the US
      this.projection = this.projection.center([-111, 48]).scale(1800);
      this.geoGenerator = d3.geoPath().projection(this.projection).context(this.context);
      return this.drawFeatures();
    },
    drawState(): Promise<void> {
      // Center and zoom on the US
      this.projection = this.projection.center([-101, 37]).scale(12000);
      this.geoGenerator = d3.geoPath()
        .projection(this.projection)
        .context(this.context);

      const oklahomaCountiesPromise = getGeoJSON('oklahomaCounties');
      const oklahomaLakesPromise = getGeoJSON('oklahomaLakes');
      const oklahomaStreamsPromise = getGeoJSON('oklahomaStreams');

      return this.drawFeatures().then(() => {
        this.drawAlerts();
        // Callback hell to allow parallel loading of geojson but
        // still draw them in the correct order
        return oklahomaCountiesPromise.then((oklahomaCounties) => {
          this.drawGeoJSON({
            stroke: 'rgba(0, 0, 0, 1)',
            strokeWidth: '1',
            fill: 'rgba(0, 0, 0, 0)',
            data: oklahomaCounties,
          });

          // Then we can draw the lakes
          return oklahomaLakesPromise.then((oklahomaLakes) => {
            this.drawGeoJSON({
              stroke: 'rgba(30, 144, 255, 1)',
              strokeWidth: '0.1',
              fill: 'rgba(30, 144, 255, 0.4)',
              data: oklahomaLakes,
            });

            // Finally we can draw the streams
            return oklahomaStreamsPromise.then((oklahomaStreams) => {
              this.drawGeoJSON({
                stroke: 'rgba(30, 144, 255, 0.8)',
                strokeWidth: '0.8',
                fill: 'rgba(0, 0, 0, 0)',
                data: oklahomaStreams,
              });
            });
          });
        });
      });
    },
    drawFeatures(nolakes: boolean = false): Promise<void> {
      const costLinePromise = getGeoJSON('coastline');
      let riversPromise = new Promise((resolve) => {
        resolve(null);
      });
      if (!nolakes) {
        riversPromise = getGeoJSON('rivers');
      }
      const statesPromise = getGeoJSON('states');
      let lakesPromise = new Promise((resolve) => {
        resolve(null);
      });
      if (!nolakes) {
        lakesPromise = getGeoJSON('lakes');
      }
      const freewaysPromise = getGeoJSON('freeways');

      return costLinePromise.then((coastline) => {
        this.drawGeoJSON({
          stroke: 'rgba(0, 0, 0, 0)',
          strokeWidth: '0',
          fill: 'rgba(255, 255, 255, 0.7)',
          data: coastline,
        });

        return riversPromise.then((rivers) => {
          if (rivers) {
            this.drawGeoJSON({
              stroke: 'rgba(30, 144, 255, 1)',
              fill: 'rgba(0, 0, 0, 0)',
              strokeWidth: '1',
              data: rivers,
            });
          }

          return statesPromise.then((states) => {
            this.drawGeoJSON({
              stroke: 'rgba(0, 0, 0, 1)',
              fill: 'rgba(0, 0, 0, 0)',
              strokeWidth: '1',
              data: states,
            });

            return lakesPromise.then((lakes) => {
              if (lakes) {
                this.drawGeoJSON({
                  stroke: 'rgba(30, 144, 255, 1)',
                  fill: 'rgba(30, 144, 255, 0.4)',
                  strokeWidth: '0.1',
                  data: lakes,
                });
              }

              return freewaysPromise.then((freeways) => {
                this.drawGeoJSON({
                  stroke: 'rgb(214, 113, 69)',
                  fill: 'rgba(0, 0, 0, 0)',
                  strokeWidth: '0.8',
                  data: freeways,
                });
              });
            });
          });
        });
      });
    },
  },
});
</script>

<style scoped>
.layered {
  width: 100%;
  display: grid;
}

.layered canvas {
  width: 100%;
}

.layered > * {
  grid-column-start: 1;
  grid-row-start: 1;
}
</style>
