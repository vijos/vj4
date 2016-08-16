import Rotator from '../rotator';
import { AutoloadPage } from '../../misc/PageLoader';
import * as util from '../../misc/Util';

function setVoteState($container, value, status) {
  const $num = $container.find('.vote-number');
  Rotator.get($num).setValue(value);
  $container.find('.vote-button').removeClass('active');
  if (status === 1) {
    $container.find('.upvote').addClass('active');
  } else if (status === -1) {
    $container.find('.downvote').addClass('active');
  }
}

function applyRotator(element) {
  Rotator.getOrConstruct($(element));
}

const votePage = new AutoloadPage(() => {
  for (const element of $('.vote-number.rotator--enabled')) {
    applyRotator(element);
  }
  $(document).on('click', '.vote-button', ev => {
    const $button = $(ev.currentTarget);
    const $container = $button.closest('.vote');
    const $form = $button.closest('form');
    util
      .post($form.attr('action'), $form)
      .then(data => {
        setVoteState($container, data.vote, data.user_vote);
      })
      .catch(() => {
        // TODO(iceboy): notify failure
      });
    return false;
  });
});

export default votePage;
