import 'highlight.js/styles/vs.css';
import hljs from 'highlight.js/lib/highlight.js';

import langCpp from 'highlight.js/lib/languages/cpp.js';
import langCs from 'highlight.js/lib/languages/cs.js';
import langDelphi from 'highlight.js/lib/languages/delphi.js';
import langJava from 'highlight.js/lib/languages/java.js';
import langJs from 'highlight.js/lib/languages/javascript.js';
import langPy from 'highlight.js/lib/languages/python.js';

hljs.registerLanguage('cpp', langCpp);
hljs.registerLanguage('cs', langCs);
hljs.registerLanguage('delphi', langDelphi);
hljs.registerLanguage('java', langJava);
hljs.registerLanguage('javascript', langJs);
hljs.registerLanguage('python', langPy);

const hljsApiWrap = {

  highlightBlocks: ($dom) => {
    $dom.find('pre code').each((i, block) => {
      hljs.highlightBlock(block);
    });
  },

};

export default hljsApiWrap;
