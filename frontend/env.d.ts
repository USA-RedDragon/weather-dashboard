/// <reference types="vite/client" />

declare global {
    interface Window {
        pyodide: {
            pyodide: any,
            azimuthRangeToLatLon: Function,
        }
    }
}

export {};
