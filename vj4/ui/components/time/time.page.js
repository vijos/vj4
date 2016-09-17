import { AutoloadPage } from '../../misc/PageLoader';
import libTimeago from 'timeago.js';
import i18n from '../../utils/i18n';

const timeago = libTimeago();
timeago.setLocale(i18n('timeago_locale'));

function runRelativeTime($container) {
  for (const element of $container.find('span.time[data-timestamp]')) {
    const $element = $(element);
    if ($element.attr('data-timeago') !== undefined) {
      continue;
    }
    $element.attr('data-tooltip', $element.text());
    $element.attr('data-timeago', ($element.attr('data-timestamp') | 0) * 1000);
    timeago.render(element);
  }
}

const relativeTimePage = new AutoloadPage(() => {
  runRelativeTime($('body'));
});

export default relativeTimePage;
