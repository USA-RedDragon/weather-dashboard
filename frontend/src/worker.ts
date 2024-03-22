/// <reference path="./worker.d.ts" />
import gcc from 'great-circle-cursor';

onmessage = (e: MessageEvent) => {
  const data = e.data as Message;
  switch (data.type) {
    case 'azimuthRangeToLatLon':
      azimuthRangeToLatLon(data.payload as azimuthRangeToLatLonOptions).then((payload) => {
        postMessage({
          payload,
          type: data.type,
        });
      });
      break;
  }
};

function meshgrid(x: number[], y: number[]): number[][][] {
  const nx = x.length;
  const ny = y.length;
  const gridX = new Array(nx) as number[][];
  const gridY = new Array(nx) as number[][];

  for (let i = 0; i < nx; i++) {
    gridX[i] = new Array(ny).fill(x[i]);
  }

  for (let j = 0; j < nx; j++) {
    gridY[j] = y;
  }

  return [gridX, gridY];
}

function full(oneDLen: number, twoDLen: number, fill: number): number[][] {
  const arr = new Array(oneDLen) as number[][];
  for (let i = 0; i < oneDLen; i++) {
    arr[i] = new Array(twoDLen).fill(fill);
  }
  return arr;
}

async function azimuthRangeToLatLon(options: azimuthRangeToLatLonOptions): Promise<azimuthRangeToLatLonResult> {
  const [az, rng] = meshgrid(options.azimuths, options.ranges);
  const xlocs = full(options.azimuths.length, options.ranges.length, options.center_lon);
  const ylocs = full(options.azimuths.length, options.ranges.length, options.center_lat);
  for (let i = 0; i < options.azimuths.length; i++) {
    for (let j = 0; j < options.ranges.length; j++) {
      const [lon, lat] = gcc([], [options.center_lon, options.center_lat], az[i][j], rng[i][j]);
      xlocs[i][j] = lon;
      ylocs[i][j] = lat;
    }
  }
  return { xlocs, ylocs, data: options.data };
}
