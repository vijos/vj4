// load all page stylesheets
const pageStyleReq = require.context('../', true, /\.page\.styl$/i);
pageStyleReq.keys().map(key => pageStyleReq(key).default);

export class Page {
  constructor(name, autoload, afterLoading, beforeLoading) {
    this.name = name;
    this.autoload = autoload;
    this.afterLoading = afterLoading;
    this.beforeLoading = beforeLoading;
  }
}

export class NamedPage extends Page {
  constructor(name = 'empty', afterLoading = function () {}, beforeLoading = function () {}) {
    super(name, false, afterLoading, beforeLoading);
  }
}

export class AutoloadPage extends Page {
  constructor(afterLoading = function () {}, beforeLoading = function () {}) {
    super('(autoload)', true, afterLoading, beforeLoading);
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
