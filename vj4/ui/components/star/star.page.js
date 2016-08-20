import { AutoloadPage } from '../../misc/PageLoader';
import * as util from '../../misc/Util';

function setStarButtonState($starButton, star) {
  if (star) {
    $starButton.addClass('activated');
  } else {
    $starButton.removeClass('activated');
  }
}

const starPage = new AutoloadPage(() => {
  $(document).on('click', '.star', (ev) => {
    const $button = $(ev.currentTarget);
    const currentState = $button.hasClass('activated');
    const $form = $button.closest('form');
    $form.find('[name="operation"]').val(currentState ? 'unstar' : 'star');
    setStarButtonState($button, !currentState);
    util
      .post($form.attr('action'), $form)
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
