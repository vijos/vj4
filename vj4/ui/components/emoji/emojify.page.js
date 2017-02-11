import emojify from 'emojify.js';

import { AutoloadPage } from '../../misc/PageLoader';

function runEmojify($container) {
  if ($container.is('[data-emoji-enabled]')) {
    emojify.run($container[0]);
    return;
  }
  $container.find('[data-emoji-enabled]').get().forEach(element => emojify.run(element));
}

const emojifyPage = new AutoloadPage(() => {
  emojify.setConfig({
    img_dir: `${UiContext.cdn_prefix}img/emoji`,
  });
  runEmojify($('body'));
  $(document).on('vjContentNew', e => runEmojify($(e.target)));
});

export default emojifyPage;
