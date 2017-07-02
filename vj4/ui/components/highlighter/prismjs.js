import Prism from 'prismjs/components/prism-core';
import 'prismjs/components/prism-clike';
import 'prismjs/components/prism-c';
import 'prismjs/components/prism-cpp';
import 'prismjs/components/prism-pascal';
import 'prismjs/components/prism-java';
import 'prismjs/components/prism-python';
import 'prismjs/components/prism-php';
import 'prismjs/components/prism-rust';
import 'prismjs/components/prism-haskell';
import 'prismjs/components/prism-javascript';
import 'prismjs/components/prism-go';
import 'prismjs/plugins/toolbar/prism-toolbar';
import 'prismjs/plugins/line-numbers/prism-line-numbers';

import Clipboard from 'clipboard';
import Notification from 'vj/components/notification';

// Copy to Clipboard
Prism.plugins.toolbar.registerButton('copy-to-clipboard', (env) => {
  const linkCopy = document.createElement('a');
  linkCopy.href = 'javascript:;'; // eslint-disable-line no-script-url
  linkCopy.textContent = 'Copy';
  const clip = new Clipboard(linkCopy, { text: () => env.code });
  clip.on('success', () => {
    Notification.success('Code copied to clipboard!', 1000);
  });
  clip.on('error', () => {
    Notification.error('Copy failed :(');
  });
  return linkCopy;
});

const prismjsApiWrap = {
  highlightBlocks: ($dom) => {
    $dom.find('pre code').get().forEach((code) => {
      const $pre = $(code).parent();
      $pre.addClass('syntax-hl');
      if ($pre.closest('[data-syntax-hl-show-line-number]')) {
        $pre.addClass('line-numbers');
      }
      Prism.highlightElement(code);
    });
  },
};

export default prismjsApiWrap;
