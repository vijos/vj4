let removalChecker = null;
const res = [];

function checkResources() {
  for (let i = res.length - 1; i >= 0; --i) {
    if (res[i].detached || !document.body.contains(res[i].$dom[0])) {
      if (!res[i].detached) {
        res[i].detach();
      }
      res.splice(i, 1);
    }
  }
  if (res.length === 0) {
    clearInterval(removalChecker);
    removalChecker = null;
  }
}

function monitorResource(resource) {
  res.push(resource);
  if (removalChecker === null) {
    removalChecker = setInterval(checkResources, 500);
  }
}

export default class DOMAttachedObject {

  static uniqueIdCounter = 0;

  static get($obj) {
    const key = this.DOMAttachKey;
    return $obj.data(key);
  }

  static getOrConstruct($obj, ...args) {
    const $singleObj = $obj.eq(0);
    const key = this.DOMAttachKey;
    const Protoclass = this;
    const instance = this.get($singleObj);
    if (instance !== undefined) {
      return instance;
    }
    const newInstance = new Protoclass($singleObj, ...args);
    $singleObj.data(key, newInstance);
    return newInstance;
  }

  detach() {
    if (this.constructor.DOMAttachKey) {
      this.$dom.removeData(this.constructor.DOMAttachKey);
    }
    this.detached = true;
  }

  constructor($dom, monitorDetach = false) {
    this.$dom = $dom;
    this.id = ++DOMAttachedObject.uniqueIdCounter;
    this.eventNS = `vj4obj_${this.id}`;
    this.detached = false;
    if (monitorDetach) {
      monitorResource(this);
    }
  }

}
