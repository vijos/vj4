export default class DOMAttachedObject {

  static uniqueIdCounter = 0;

  static get($obj) {
    const key = this.DOMAttachKey;
    return $obj.data(key);
  }

  static getOrConstruct($obj, ...args) {
    const key = this.DOMAttachKey;
    const Protoclass = this;
    const instance = this.get($obj);
    if (instance !== undefined) {
      return instance;
    }
    const newInstance = new Protoclass($obj, ...args);
    $obj.data(key, newInstance);
    return newInstance;
  }

  static from(Protoclass, key, $obj, ...args) {
    const instance = $obj.data(key);
    if (instance !== undefined) {
      return instance;
    }
    const newInstance = new Protoclass($obj, ...args);
    $obj.data(key, newInstance);
    return newInstance;
  }

  detach() {
    if (this.constructor.DOMAttachKey) {
      this.$dom.removeData(this.constructor.DOMAttachKey);
    }
  }

  constructor($dom) {
    this.$dom = $dom;
    this.id = ++DOMAttachedObject.uniqueIdCounter;
    this.eventNS = `vj4obj_${this.id}`;
  }

}
