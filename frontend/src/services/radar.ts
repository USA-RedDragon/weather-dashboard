/// <reference path="./radar.d.ts" />

import axios from 'axios';
import { decode } from '@msgpack/msgpack';

class RadarListener extends EventTarget {
  private timestamp: number;
  private station: string;

  constructor(station: string, startingTimestamp: number) {
    super();
    this.station = station;
    this.timestamp = startingTimestamp;
  }

  async start() {
    setInterval(() => {
      this.checkForNewScan();
    }, 5000);
  }

  checkForNewScan() {
    axios.get(`/api/radar/${this.station}/scan/0`).then((resp) => {
      resp.data.timestamp *= 1000;
      if (resp.data.timestamp > this.timestamp) {
        this.timestamp = resp.data.timestamp;
        this.dispatchEvent(new Event('scan'));
      }
    });
  }
}

export const listenForNewScan = (
  station: string, sweep: number, startingTimestamp: number, callback: (_scan: radarScan) => void,
): () => void => {
  const listener = new RadarListener(station, startingTimestamp);
  const wrappedCb = () => {
    getScan(station, sweep).then(callback);
  };
  listener.addEventListener('scan', wrappedCb);
  listener.start();
  return () => {
    listener.removeEventListener('scan', wrappedCb);
  };
};

export const getScan = async (station: string, sweep: number): Promise<radarScan> => {
  // Fire and forget
  clearOldCaches();

  const resp = await axios.get(`/api/radar/${station}/scan/0`);
  const scanTime = resp.data.timestamp;

  const cacheKey = `radar-${station}-${sweep}-${scanTime}`;
  const cache = await caches.open(cacheKey);
  const request = new Request(`/api/radar/${station}/${sweep}/${scanTime}`);
  const response = await cache.match(request);
  if (response && response.status === 200) {
    const blob = await response.blob();
    const arrayBuffer = await blob.arrayBuffer();
    return decode(arrayBuffer) as radarScan;
  }
  const dataResponse = await axios.get(request.url, { responseType: 'arraybuffer' });
  if (dataResponse.status !== 200) {
    throw new Error(`Failed to fetch radar data: ${dataResponse.status} ${dataResponse.statusText}`);
  }
  await cache.put(request, new Response(
    dataResponse.data,
    { status: dataResponse.status, statusText: dataResponse.statusText },
  ));
  return decode(dataResponse.data) as radarScan;
};

export const colormap = (value: number): number => {
  if (value <= -30) {
    return 0x764fab;
  } else if (value <= -25) {
    return 0x7c689a;
  } else if (value <= -20) {
    return 0x86818e;
  } else if (value <= -15) {
    return 0xaeaea3;
  } else if (value <= -10) {
    return 0xcccc99;
  } else if (value <= -5) {
    return 0x9ba1a6;
  } else if (value <= 0) {
    return 0x77819d;
  } else if (value <= 5) {
    return 0x5a6c9f;
  } else if (value <= 10) {
    return 0x405aa0;
  } else if (value <= 15) {
    return 0x419b96;
  } else if (value <= 20) {
    return 0x40d38d;
  } else if (value <= 25) {
    return 0x20af45;
  } else if (value <= 30) {
    return 0x018d01;
  } else if (value <= 35) {
    return 0x83b100;
  } else if (value <= 40) {
    return 0xeed000;
  } else if (value <= 45) {
    return 0xf6ad00;
  } else if (value <= 50) {
    return 0xf70000;
  } else if (value <= 55) {
    return 0xdf0000;
  } else if (value <= 60) {
    return 0xffc9ff;
  } else if (value <= 65) {
    return 0xffabfb;
  } else if (value <= 70) {
    return 0xad00ff;
  } else if (value <= 75) {
    return 0xa200f9;
  } else if (value <= 80) {
    return 0x00e1ec;
  } else {
    return 0x3333cc;
  }
};

async function clearOldCaches() {
  // Delete any cached entries with scanTimes older than 1 hour
  const anHourAgo = Date.now() - 3600000;
  const unixTime = Math.floor(anHourAgo / 1000);
  const keys = await caches.keys();
  for (const key of keys) {
    // key is radar-{station}-{sweep}-{scanTime}
    const parts = key.split('-');
    if (parts.length !== 4) {
      continue;
    }
    const scanTime = parseInt(parts[3], 10);
    if (scanTime < unixTime) {
      console.log(`Deleting old cache: ${key}`);
      await caches.delete(key);
    }
  }
}
