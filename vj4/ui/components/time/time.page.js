import Timeago from 'timeago.js';

import { AutoloadPage } from 'vj/misc/PageLoader';

import i18n from 'vj/utils/i18n';

function runRelativeTime($container) {
  $container.find('span.time.relative[data-timestamp]').get().forEach((element) => {
    const $element = $(element);
    if ($element.data('timeago') !== undefined) {
      return;
    }
    const timeago = new Timeago();
    timeago.setLocale(i18n('timeago_locale'));
    $element.attr('data-tooltip', $element.text());
    $element.attr('datetime', ($element.attr('data-timestamp') || 0) * 1000);
    timeago.render(element);
    $element.data('timeago', timeago);
  });
}

function cancelRelativeTime($container) {
  $container.find('span.time.relative[data-timestamp]').get().forEach((element) => {
    const $element = $(element);
    const timeago = $element.data('timeago');
    if (timeago === undefined) {
      return;
    }
    timeago.cancel();
    $element.removeData('timeago');
  });
}

const relativeTimePage = new AutoloadPage('relativeTimePage', () => {
  runRelativeTime($('body'));
  $(document).on('vjContentNew', e => runRelativeTime($(e.target)));
  $(document).on('vjContentRemove', e => cancelRelativeTime($(e.target)));
});

export default relativeTimePage;
