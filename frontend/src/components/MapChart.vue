<template>
  <canvas></canvas>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import * as d3 from 'd3';
import { getGeoJSON as geoJSON } from '../services/geojson';
import * as radar from '../services/radar';
import type radarScan from '../services/radar';

type data = {
  height: number;
  width: number;
  projection: d3.GeoProjection;
  geoGenerator: d3.GeoPath | null;
  canvas: d3.Selection<d3.BaseType, unknown, HTMLElement, any> | null;
  detachedContainer: HTMLElement;
  dataContainer: d3.Selection<HTMLElement, unknown, null, undefined>;
  context: CanvasRenderingContext2D | null;
}

type drawGeoJSONOptions = {
  stroke: string,
  fill: string,
  strokeWidth: string,
  data: any,
}

export default defineComponent({
  components: { },
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
  },
  data: (): data => {
    const detachedContainer = document.createElement('custom');

    return {
      height: 1080,
      width: 1920,
      projection: d3.geoEquirectangular(),
      geoGenerator: null,
      detachedContainer,
      dataContainer: d3.select(detachedContainer),
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

    if (this.country) {
      this.drawCountry();
    } else if (this.state) {
      this.drawState();
    }
  },
  methods: {
    drawRadar(data: radarScan) {
      if (!this.geoGenerator) {
        console.error('geoGenerator is null');
        return;
      }

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
    drawCountry() {
      // Center and zoom on the US
      this.projection = this.projection.center([-111, 48]).scale(1800);
      this.geoGenerator = d3.geoPath().projection(this.projection).context(this.context);
      this.drawFeatures();
    },
    async drawState() {
      // Center and zoom on the US
      this.projection = this.projection.center([-101, 37]).scale(12000);
      this.geoGenerator = d3.geoPath()
        .projection(this.projection)
        .context(this.context);

      const oklahomaCountiesPromise = geoJSON('oklahomaCounties');
      const oklahomaLakesPromise = geoJSON('oklahomaLakes');
      const oklahomaStreamsPromise = geoJSON('oklahomaStreams');
      const radarPromise = radar.getScan('ktlx');

      // Callback hell to allow parallel loading of geojson but
      // still draw them in the correct order
      return this.drawFeatures(true).then(() => {
        // Then we can draw the counties
        oklahomaCountiesPromise.then((oklahomaCounties) => {
          this.drawGeoJSON({
            stroke: 'rgba(0, 0, 0, 1)',
            strokeWidth: '1',
            fill: 'rgba(0, 0, 0, 0)',
            data: oklahomaCounties,
          });

          // Then we can draw the lakes
          oklahomaLakesPromise.then((oklahomaLakes) => {
            this.drawGeoJSON({
              stroke: 'rgba(30, 144, 255, 1)',
              strokeWidth: '0.1',
              fill: 'rgba(30, 144, 255, 0.4)',
              data: oklahomaLakes,
            });

            // Then we can draw the streams
            oklahomaStreamsPromise.then((oklahomaStreams) => {
              this.drawGeoJSON({
                stroke: 'rgba(30, 144, 255, 0.8)',
                strokeWidth: '0.8',
                fill: 'rgba(0, 0, 0, 0)',
                data: oklahomaStreams,
              });

              // Finally we can draw the radar on top
              radarPromise.then((radar) => {
                this.drawRadar(radar);
              });
            });
          });
        });
      });
    },
    async drawFeatures(nolakes: boolean = false) {
      const costLinePromise = geoJSON('coastline');
      let riversPromise = new Promise((resolve) => {
        resolve(null);
      });
      if (!nolakes) {
        riversPromise = geoJSON('rivers');
      }
      const statesPromise = geoJSON('states');
      let lakesPromise = new Promise((resolve) => {
        resolve(null);
      });
      if (!nolakes) {
        lakesPromise = geoJSON('lakes');
      }
      const freewaysPromise = geoJSON('freeways');

      return costLinePromise.then((coastline) => {
        this.drawGeoJSON({
          stroke: 'rgba(0, 0, 0, 0)',
          strokeWidth: '0',
          fill: 'rgba(255, 255, 255, 0.7)',
          data: coastline,
        });

        riversPromise.then((rivers) => {
          if (rivers) {
            this.drawGeoJSON({
              stroke: 'rgba(30, 144, 255, 1)',
              fill: 'rgba(0, 0, 0, 0)',
              strokeWidth: '1',
              data: rivers,
            });
          }

          statesPromise.then((states) => {
            this.drawGeoJSON({
              stroke: 'rgba(0, 0, 0, 1)',
              fill: 'rgba(0, 0, 0, 0)',
              strokeWidth: '1',
              data: states,
            });

            lakesPromise.then((lakes) => {
              if (lakes) {
                this.drawGeoJSON({
                  stroke: 'rgba(30, 144, 255, 1)',
                  fill: 'rgba(30, 144, 255, 0.4)',
                  strokeWidth: '0.1',
                  data: lakes,
                });
              }

              freewaysPromise.then((freeways) => {
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
canvas {
  width: 100%;
}
</style>
