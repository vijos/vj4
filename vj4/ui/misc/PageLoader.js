// load all page stylesheets
require.context('../', true, /\.page\.styl$/i);

export class Page {
  constructor(name, autoload, beforeLoading, afterLoading) {
    this.name = name;
    this.autoload = autoload;
    this.beforeLoading = beforeLoading;
    this.afterLoading = afterLoading;
  }
}

export class NamedPage extends Page {
  constructor(name = 'empty', beforeLoading = function () {}, afterLoading = function () {}) {
    super(name, false, beforeLoading, afterLoading);
  }
}

export class AutoloadPage extends Page {
  constructor(beforeLoading = function () {}, afterLoading = function () {}) {
    super(null, true, beforeLoading, afterLoading);
  }
}

export class PageLoader {
  constructor() {
    const pageReq = require.context('../', true, /\.page\.js$/i);
    this.pageInstances = pageReq.keys().map(key => pageReq(key).default);
  }

  getAutoloadPages() {
    const pages = this.pageInstances.filter(page => page.autoload);
    return pages;
  }

  getNamedPage(pageName) {
    const pages = this.pageInstances.filter(page => page.name === pageName);
    if (pages.length > 0) {
      return pages[0];
    }
    return new NamedPage();
  }
}
