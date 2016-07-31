import { AutoloadPage } from '../../misc/PageLoader';
import * as util from '../../misc/Util';

function setStarButtonState($starButton, star) {
  const $starIcon = $starButton.find('.icon');
  if (star) {
    $starButton.addClass('activated');
    $starIcon.removeClass('icon-star--outline').addClass('icon-star');
  } else {
    $starButton.removeClass('activated');
    $starIcon.removeClass('icon-star').addClass('icon-star--outline');
  }
}

const starPage = new AutoloadPage(() => {
  $(document).on('click', '.star', (ev) => {
    const $button = $(ev.currentTarget);
    const currentState = $button.hasClass('activated');
    const operation = currentState ? 'unstar' : 'star';
    const pid = $button.closest('tr').attr('data-pid');
    setStarButtonState($button, !currentState);
    util
      .post($button.closest('form').attr('action'), {
        operation,
        pid,
      })
      .then(data => {
        setStarButtonState($button, data.star);
      })
      .catch(() => {
        // TODO: notify failure
        setStarButtonState($button, currentState);
      });
    return false;
  });
});

export default starPage;
