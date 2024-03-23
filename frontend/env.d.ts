/// <reference types="vite/client" />
/// <reference path="./src/worker.d.ts" />
/// <reference path="./src/services/radar.d.ts" />
/// <reference path="./src/services/alerts.d.ts" />

declare global {
    interface Window {
        worker: Worker,
    }
}

export {};
