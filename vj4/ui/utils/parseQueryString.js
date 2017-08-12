export default function parseQueryString(str) {
  const obj = {};
  (str || document.location.search)
    .replace(/(^\?)/, '')
    .split('&')
    .forEach((n) => {
      const s = n.split('=').map(v => decodeURIComponent(v));
      obj[s[0]] = s[1];
    });
  return obj;
}
