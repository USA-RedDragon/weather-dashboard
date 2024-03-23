export function getWebsocketURI(path: string) {
  const loc = window.location;
  let newURI;
  if (loc.protocol === 'https:') {
    newURI = 'wss:';
  } else {
    newURI = 'ws:';
  }
  newURI += '//' + loc.host + `/ws/${path}`;
  console.log('Websocket URI: "' + newURI + '"');
  return newURI;
}
