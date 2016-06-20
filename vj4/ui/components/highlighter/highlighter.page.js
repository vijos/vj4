import { AutoloadPage } from '../../misc/PageLoader';
import hljs from '../highlighter/hljs';

const highlighterPage = new AutoloadPage(() => {
  hljs.highlightBlocks($('body'));
});

export default highlighterPage;
