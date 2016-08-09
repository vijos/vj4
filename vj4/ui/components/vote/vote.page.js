import { AutoloadPage } from '../../misc/PageLoader';
import * as util from '../../misc/Util';

function setVoteState($voteLi, vote) {
  const $voteCount = $voteLi.find('.vote--count');
  $voteCount.text(vote);
}

const votePage = new AutoloadPage(() => {
  $(document).on('click', '.vote', (ev) => {
    const $button = $(ev.currentTarget);
    const $li = $button.closest('li');
    const operation = $button.hasClass('vote--upvote') ? 'upvote' : 'downvote';
    const psid = $li.attr('data-psid');
    util
      .post($button.closest('form').attr('action'), {
        operation,
        psid,
      })
      .then(data => {
        setVoteState($li, data.vote);
      })
      .catch(() => {
        // TODO(iceboy): notify failure
      });
    return false;
  });
});

export default votePage;
