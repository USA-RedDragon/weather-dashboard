/// <reference path="./worker.d.ts" />
import { getFunctions } from './pyodide';

let functions: {
    azimuthRangeToLatLon: Function,
} | null = null;
getFunctions().then((f) => functions = f as any);

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

async function azimuthRangeToLatLon(options: azimuthRangeToLatLonOptions): Promise<azimuthRangeToLatLonResult> {
  while (!functions) {
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  const [xlocs, ylocs] = (functions.azimuthRangeToLatLon(
    options.azimuths,
    options.ranges,
    options.center_lon,
    options.center_lat,
  ).toJs() as [number[][], number[][]]);

  return { xlocs, ylocs, data: options.data };
}
