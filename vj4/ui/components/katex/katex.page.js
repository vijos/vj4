import { AutoloadPage } from 'vj/misc/PageLoader';

const katexPage = new AutoloadPage(async () => {
  const renderKatex = System.import('katex/dist/contrib/auto-render.min.js');
  async function runKatex($container) {
    (await renderKatex)($container[0]);
  }
  runKatex($('body'));
  $(document).on('vjContentNew', e => runKatex($(e.target)));
});

export default katexPage;
