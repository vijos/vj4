// TODO(swx): Use a custom theme.
import 'prismjs/themes/prism.css';
import prismjs from 'prismjs/prism.js';

import 'prismjs/components/prism-c.js';
import 'prismjs/components/prism-cpp.js';
import 'prismjs/components/prism-pascal.js';
import 'prismjs/components/prism-java.js';
import 'prismjs/components/prism-python.js';
import 'prismjs/components/prism-php.js';
import 'prismjs/components/prism-rust.js';
import 'prismjs/components/prism-haskell.js';

const prismjsApiWrap = {
  highlightBlocks: ($dom) => {
    $dom.find('pre code').get().forEach(block => prismjs.highlightElement(block));
  },
};

export default prismjsApiWrap;
