const initialReconnectDelay = 300;
const maxReconnectDelay = 15000;

export class Websocket {
  url: string;
  timeoutTimer: any;
  timeout: number;
  socket: WebSocket | null;
  onMessage: (_ev: MessageEvent) => void;
  currentReconnectDelay: number;
  connected: boolean;

  constructor(url: string, onMessage: (_ev: MessageEvent) => void) {
    this.url = url;
    this.timeoutTimer = null;
    this.timeout = 3000;
    this.socket = null;
    this.onMessage = onMessage;
    this.currentReconnectDelay = initialReconnectDelay;
    this.connected = false;
  }

  connect() {
    this.socket = new WebSocket(this.url);
    this.mapSocketEvents();
  }

  cleanup() {
    if (this.socket) {
      try {
        this.socket.send('close');
      } catch (e: any) {
        if (e.name !== 'DOMException') {
          throw e;
        }
        console.log('Socket already closed');
      }
      this.socket?.close();
    }
  }

  onWebsocketOpen() {
    console.log('Connected to websocket');
    this.connected = true;
    this.currentReconnectDelay = initialReconnectDelay;
  }

  onWebsocketError() {
    console.log('Disconnected from websocket');
    this.socket = null;
    this.reconnectToWebsocket();
  }

  onWebsocketClose() {
    console.log('Websocket closed');
    this.socket = null;
    if (this.connected) {
      this.reconnectToWebsocket();
    }
  }

  reconnectToWebsocket() {
    this.connected = false;
    setTimeout(() => {
      if (this.currentReconnectDelay < maxReconnectDelay) {
        this.currentReconnectDelay *= 2;
      }
      this.connect();
    }, this.currentReconnectDelay + Math.floor(Math.random() * 1000));
  }

  mapSocketEvents() {
    this.socket!.addEventListener('open', this.onWebsocketOpen.bind(this));
    this.socket!.addEventListener('error', this.onWebsocketError.bind(this));
    this.socket!.addEventListener('close', this.onWebsocketClose.bind(this));

    this.socket!.addEventListener('message', (event) => {
      this.connected = true;
      if (event.data == 'PONG') {
        setTimeout(() => {
          this.socket?.send('PING');
        }, 1000);
        return;
      } else {
        this.onMessage(event);
      }
    });
  }
}

export const connectWebsocket = (url: string, onMessage: (_ev: MessageEvent) => void) => {
  const ws = new Websocket(url, onMessage);
  ws.connect();
  return ws;
};
