import { AutoloadPage } from 'vj/misc/PageLoader';
import prismjs from 'vj/components/highlighter/prismjs';

function runHighlight($container) {
  prismjs.highlightBlocks($container);
}

const highlighterPage = new AutoloadPage('highlighterPage', () => {
  runHighlight($('body'));
  $(document).on('vjContentNew', e => runHighlight($(e.target)));
});

export default highlighterPage;
