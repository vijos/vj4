import { AutoloadPage } from '../../misc/PageLoader';

const katexPage = new AutoloadPage(async () => {
  const katex = await System.import('katex');
  function runKatex($container) {
    for (const element of $container.find('code')) {
      const $element = $(element);
      const text = $element.text();
      let formula = null;
      let $outer = null;
      let isInline = null;
      if ($element.parent().is('pre') && $element.is('.language-math')) {
        formula = text;
        $outer = $element.parent();
        isInline = false;
      } else if (text.match(/^\$/) && text.match(/\$$/) && text.length > 2) {
        formula = text.substr(1, text.length - 2);
        $outer = $element;
        isInline = true;
      } else {
        continue;
      }
      const $wrap = $('<span>');
      try {
        katex.render(formula, $wrap[0], {
          displayMode: !isInline,
        });
        $outer.replaceWith($wrap);
      } catch (ex) {
        // ignore
      }
    }
  }
  runKatex($('body'));
  $(document).on('vjContentNew', e => runKatex($(e.target)));
});

export default katexPage;
