import axios from 'axios';
import { decode } from '@msgpack/msgpack';

type radarScan = {
  xlocs: number[];
  ylocs: number[];
  data: number[];
  timestamp: number;
}

export const getScan = async (station: string, sweep: number = 0.0): Promise<radarScan> => {
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

export const colormap = (value: number): string => {
  if (value <= -30) {
    return '#764fab';
  } else if (value <= -25) {
    return '#7c689a';
  } else if (value <= -20) {
    return '#86818e';
  } else if (value <= -15) {
    return '#aeaea3';
  } else if (value <= -10) {
    return '#cccc99';
  } else if (value <= -5) {
    return '#9ba1a6';
  } else if (value <= 0) {
    return '#77819d';
  } else if (value <= 5) {
    return '#5a6c9f';
  } else if (value <= 10) {
    return '#405aa0';
  } else if (value <= 15) {
    return '#419b96';
  } else if (value <= 20) {
    return '#40d38d';
  } else if (value <= 25) {
    return '#20af45';
  } else if (value <= 30) {
    return '#018d01';
  } else if (value <= 35) {
    return '#83b100';
  } else if (value <= 40) {
    return '#eed000';
  } else if (value <= 45) {
    return '#f6ad00';
  } else if (value <= 50) {
    return '#f70000';
  } else if (value <= 55) {
    return '#df0000';
  } else if (value <= 60) {
    return '#ffc9ff';
  } else if (value <= 65) {
    return '#ffabfb';
  } else if (value <= 70) {
    return '#ad00ff';
  } else if (value <= 75) {
    return '#a200f9';
  } else if (value <= 80) {
    return '#00e1ec';
  } else {
    return '#3333cc';
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
