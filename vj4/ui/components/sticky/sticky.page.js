import { AutoloadPage } from '../../misc/PageLoader';

import responsiveCutoff from '../../responsive.inc.js';
import 'sticky-kit/dist/sticky-kit';
import _ from 'lodash';

function updateStickies($stickies) {
  const ww = window.innerWidth;
  $stickies.each((i, element) => {
    const $sticky = $(element);
    const shouldEnableSticky = (ww >= $sticky.data('sticky-cutoff-min'));
    const stickyEnabled = $sticky.data('sticky-enabled');
    if (shouldEnableSticky && !stickyEnabled) {
      const stickyOptions = {};
      const $stickyParent = $sticky.closest('[data-sticky-parent]');
      if ($stickyParent.length > 0) {
        stickyOptions.parent = $stickyParent;
      }
      const $nav = $('.nav');
      if ($nav.length > 0) {
        stickyOptions.offset_top = $nav.height() + 10;
      } else {
        stickyOptions.offset_top = 10;
      }
      $sticky.stick_in_parent(stickyOptions);
      $sticky.data('sticky-enabled', true);
    } else if (!shouldEnableSticky && stickyEnabled) {
      $sticky.trigger('sticky_kit:detach');
      $sticky.data('sticky-enabled', false);
    }
  });
}

function getCutoff(str) {
  if (str === 'medium') {
    return responsiveCutoff.mobile;
  } else if (str === 'large') {
    return responsiveCutoff.desktop;
  }
  return 0;
}

const stickyPage = new AutoloadPage(() => {
  let shouldListenResize = false;
  const $stickies = $('[data-sticky]');
  $stickies.each((i, element) => {
    const $sticky = $(element);
    const minEnabledSize = $sticky.attr('data-sticky');
    if (minEnabledSize === 'medium' || minEnabledSize === 'large') {
      shouldListenResize = true;
    }
    $sticky.data('sticky-cutoff-min', getCutoff(minEnabledSize));
    $sticky.data('sticky-enabled', false);
  });
  updateStickies($stickies);
  if (shouldListenResize) {
    $(window).on('resize', _.throttle(() => updateStickies($stickies), 300));
  }
});

export default stickyPage;
