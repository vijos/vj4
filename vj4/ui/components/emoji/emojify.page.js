import { AutoloadPage } from '../../misc/PageLoader';
import emojify from 'emojify.js';

function runEmojify($container) {
  if ($container.is('[data-emoji-enabled]')) {
    emojify.run($container[0]);
    return;
  }
  for (const element of $container.find('[data-emoji-enabled]')) {
    emojify.run(element);
  }
}

const emojifyPage = new AutoloadPage(() => {
  emojify.setConfig({
    img_dir: `${UiContext.cdn_prefix}img/emoji`,
  });
  runEmojify($('body'));
  $(document).on('vjContentNew', e => runEmojify($(e.target)));
});

export default emojifyPage;
