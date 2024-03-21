// This module will download map data from the server at /api/geojson/{data}
// and keep it in IndexedDB storage for caching and lazy-loading purposes.

// data can be one of the following:
// - coastline
// - states
// - lakes
// - rivers
// - freeways
// - oklahomaCounties
// - oklahomaLakes
// - oklahomaStreams

type dataType = 'coastline' |
    'states' |
    'lakes' |
    'rivers' |
    'freeways' |
    'oklahomaCounties' |
    'oklahomaLakes' |
    'oklahomaStreams';

// We'll split this out to different versions if needed in the future,
// but for now, all the caches are the same version.
const currentVersion = 1;

export const getGeoJSON = async (data: dataType): Promise<any> => {
  const cacheKey = `geojson-${data}-${currentVersion}`;
  const cache = await caches.open(cacheKey);
  const request = new Request(`/api/geojson/${data}/${currentVersion}`);
  const response = await cache.match(request);
  if (response && response.status === 200) {
    return response.json();
  }
  const dataResponse = await fetch(request);
  await cache.put(request, dataResponse.clone());
  return dataResponse.json();
};
