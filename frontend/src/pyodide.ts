import { loadPyodide } from 'pyodide';

async function cacheDep(cache: Cache, name: string) {
  const request = new Request(`/node_modules/pyodide/${name}`);
  const response = await cache.match(request);
  if (response && response.status === 200) {
    return;
  }
  const dataResponse = await fetch(request);
  await cache.put(request, dataResponse.clone());
}

(async () => {
  const cache = await caches.open(`pyodide`);

  await Promise.all([
    cacheDep(cache, 'pyodide.asm.wasm'),
    cacheDep(cache, 'python_stdlib.zip'),
    cacheDep(cache, 'numpy-1.26.1-cp311-cp311-emscripten_3_1_46_wasm32.whl'),
    cacheDep(cache, 'pyproj-3.4.1-cp311-cp311-emscripten_3_1_46_wasm32.whl'),
    cacheDep(cache, 'certifi-2023.7.22-py3-none-any.whl'),
    cacheDep(cache, 'sqlite3-1.0.0.zip'),
  ]);

  const _pyodide = await loadPyodide({
    fullStdLib: false,
    packages: ['numpy', 'pyproj', 'certifi', 'sqlite3'],
  });

  _pyodide.runPython(`
    import numpy as np
    import pyproj
    def azimuth_range_to_lat_lon(azimuths, ranges, center_lon, center_lat):
      rng2d, az2d = np.meshgrid(ranges, azimuths)
      lats = np.full(az2d.shape, center_lat)
      lons = np.full(az2d.shape, center_lon)
      lon, lat, _ = pyproj.Geod(ellps='sphere').fwd(lons, lats, az2d, rng2d)
      return lon.tolist(), lat.tolist()
  `);

  window.pyodide = {
    pyodide: _pyodide,
    azimuthRangeToLatLon: _pyodide.globals.get('azimuth_range_to_lat_lon') as Function,
  };
})();
