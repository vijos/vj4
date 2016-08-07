import { AutoloadPage } from '../../misc/PageLoader';
import emojify from 'emojify.js';

import 'emojify.js/dist/css/basic/emojify.css';

function runEmojify($container) {
  $container.find('.emoji--enabled').each((i, element) => {
    emojify.run(element);
  });
}

const emojifyPage = new AutoloadPage(() => {
  emojify.setConfig({
    img_dir: `${UiContext.cdn_prefix}img/emoji`,
  });
  runEmojify($('body'));
  $(document).on('vj.content.new', e => runEmojify($(e.target)));
});

export default emojifyPage;
