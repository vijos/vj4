import { AutoloadPage } from 'misc/PageLoader';
import * as util from 'misc/Util';

function setStarButtonState($starButton, star) {
  const $starIcon = $starButton.find('i');
  if (star) {
    $starButton.removeClass('star--outline').addClass('star--fill');
    $starIcon.removeClass('icon-star-empty').addClass('icon-star-full');
  } else {
    $starButton.removeClass('star--fill').addClass('star--outline');
    $starIcon.removeClass('icon-star-full').addClass('icon-star-empty');
  }
}

const starPage = new AutoloadPage(() => {

  $(document).on('click', '.star', (ev) => {
    const $button = $(ev.currentTarget);
    const currentState = $button.hasClass('star--fill');
    const operation = currentState ? 'unstar' : 'star';
    const pid = $button.closest('tr').attr('data-pid');
    setStarButtonState($button, !currentState);
    util.post($button.closest('form').attr('action'), {
      operation,
      pid,
    })
      .done(data => {
        setStarButtonState($button, data.star);
      })
      .fail(() => {
        // TODO: notify failure
        setStarButtonState($button, currentState);
      });
    return false;
  });

});

export default starPage;
