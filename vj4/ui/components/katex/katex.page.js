import { AutoloadPage } from '../../misc/PageLoader';

const katexPage = new AutoloadPage(async () => {
  const renderKatex = await System.import('katex/dist/contrib/auto-render.min.js');
  function runKatex($container) {
    renderKatex($container[0]);
  }
  runKatex($('body'));
  $(document).on('vjContentNew', e => runKatex($(e.target)));
});

export default katexPage;
