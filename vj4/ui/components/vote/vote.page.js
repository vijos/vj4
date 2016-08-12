import Odometer from 'odometer';

import { AutoloadPage } from '../../misc/PageLoader';
import * as util from '../../misc/Util';

function setVoteState($container, value, status) {
  const $num = $container.find('.vote-number');
  $num.text(value);
  $container.find('.vote-button').removeClass('active');
  if (status === 1) {
    $container.find('.upvote').addClass('active');
  } else if (status === -1) {
    $container.find('.downvote').addClass('active');
  }
}

function applyOdometer(element) {
  $(element).data('odometer', new Odometer({
    el: element,
    duration: 200,
    format: 'd',
    value: $(element).text(),
  }));
}

const votePage = new AutoloadPage(() => {
  $('.vote-number.odometer--enabled').each((i, el) => applyOdometer(el));
  $(document).on('click', '.vote-button', ev => {
    const $button = $(ev.currentTarget);
    const $container = $button.closest('.vote');
    const $form = $button.closest('form');
    util
      .post($form.attr('action'), $form)
      .then(data => {
        // TODO: fix new status
        // TODO: apply initial status (add `active` class) in HTML
        const newStatus = $button.is('.upvote') ? 1 : -1;
        setVoteState($container, data.vote, newStatus);
      })
      .catch(() => {
        // TODO(iceboy): notify failure
      });
    return false;
  });
});

export default votePage;
