<template>
  <div>
    <div v-if="radar">
      <p>Radar Scan: {{currentTimestamp.toString()}}</p>
      <br />
      <p>Sweep Angle</p>
      <!-- @vue-expect-error PrimeVue doesn't have the proper
          type, only Nullable<string>, but passing a string
          value breaks the component -->
      <InputText v-model.number="sweep" class="w-14rem"></InputText>
      <Slider v-model="sweep" :step="1" :max="7" class="w-14rem"></Slider>
      <br />
    </div>
    <div class="layered">
      <canvas></canvas>
      <RadarCanvas
        v-if="radar"
        @timestamp="updateTimestamp"
        :projection="projection"
        :sweep="sweep"
        :width="width"
        :height="height" />
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import * as d3 from 'd3';
import InputText from 'primevue/inputtext';
import Slider from 'primevue/slider';
import { getGeoJSON } from '../services/geojson';
import RadarCanvas from './RadarCanvas.vue';

type data = {
  height: number;
  width: number;
  sweep: number;
  currentTimestamp: string | Date;
  projection: d3.GeoProjection;
  geoGenerator: d3.GeoPath | null;
  canvas: d3.Selection<d3.BaseType, unknown, HTMLElement, any> | null;
  context: CanvasRenderingContext2D | null;
}

type drawGeoJSONOptions = {
  stroke: string,
  fill: string,
  strokeWidth: string,
  data: any,
}

export default defineComponent({
  components: {
    InputText,
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
      projection: d3.geoEquirectangular(),
      geoGenerator: null,
      currentTimestamp: 'Loading...',
      canvas: null,
      context: null,
    };
  },
  mounted() {
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
    updateTimestamp(ts: string | Date) {
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
