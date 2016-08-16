import 'highlight.js/styles/vs.css';
import hljs from 'highlight.js/lib/highlight.js';

import langCpp from 'highlight.js/lib/languages/cpp.js';
import langDelphi from 'highlight.js/lib/languages/delphi.js';
import langJava from 'highlight.js/lib/languages/java.js';
import langPy from 'highlight.js/lib/languages/python.js';

hljs.registerLanguage('cpp', langCpp);
hljs.registerLanguage('delphi', langDelphi);
hljs.registerLanguage('java', langJava);
hljs.registerLanguage('python', langPy);

const hljsApiWrap = {

  highlightBlocks: ($dom) => {
    for (const block of $dom.find('pre code')) {
      hljs.highlightBlock(block);
    }
  },

};

export default hljsApiWrap;
