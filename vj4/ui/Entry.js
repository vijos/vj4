import 'jquery.transit';

import 'normalize.css/normalize.css';
import 'codemirror/lib/codemirror.css';

import _ from 'lodash';

import './misc/float.styl';
import './misc/typography.styl';
import './misc/textalign.styl';
import './misc/grid.styl';
import './misc/slideout.styl';

import './misc/.iconfont/webicon.styl';
import './misc/immersive.styl';
import './misc/structure.styl';
import './misc/section.styl';
import './misc/nothing.styl';

import { PageLoader } from './misc/PageLoader';
import delay from './utils/delay';

// eslint-disable-next-line camelcase
__webpack_public_path__ = UiContext.cdn_prefix;

const pageLoader = new PageLoader();

const currentPage = pageLoader.getNamedPage(document.documentElement.getAttribute('data-page'));
const includedPages = pageLoader.getAutoloadPages();

async function load() {
  const loadSequence = [
    ...includedPages.map(p => [p.beforeLoading, p]),
    [currentPage.beforeLoading, currentPage],
    ...includedPages.map(p => [p.afterLoading, p]),
    [currentPage.afterLoading, currentPage],
  ];
  for (const [func, page] of loadSequence) {
    if (typeof func !== 'function') {
      continue;
    }
    try {
      await func();
    } catch (e) {
      console.error(`Failed to load page ${page.name}\n${e.stack}`);
    }
  }
  const sections = _.map($('.section').get(), (section, idx) => ({
    shouldDelay: idx < 5, // only animate first 5 sections
    $element: $(section),
  }));
  for (const { $element, shouldDelay } of sections) {
    $element.addClass('visible');
    if (shouldDelay) {
      await delay(50);
    }
  }
  await delay(500);
  for (const { $element } of sections) {
    $element.trigger('vjLayout');
  }
  $(document).trigger('vjPageFullyInitialized');
}

load();
