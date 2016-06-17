// eslint-disable-next-line camelcase
__webpack_public_path__ = UiContext.cdn_prefix;

import 'jquery.transit';

import 'normalize.css/normalize.css';
import 'balloon-css/balloon.min.css';
import 'jqmath-build/webpack.js';
import 'codemirror/lib/codemirror.css';

import './misc/clearfix.styl';
import './misc/typography.styl';
import './misc/webicon.css';
import './misc/immersive.styl';
import './misc/autoexpand.styl';
import './misc/structure.styl';
import './misc/section.styl';
import './misc/nothing.styl';

import { PageLoader } from './misc/PageLoader';

const pageLoader = new PageLoader();

const currentPage = pageLoader.getNamedPage(document.documentElement.getAttribute('data-page'));
const includedPages = pageLoader.getAutoloadPages();

includedPages.forEach(p => p.beforeLoading());
currentPage.beforeLoading();

includedPages.forEach(p => p.afterLoading());
currentPage.afterLoading();
