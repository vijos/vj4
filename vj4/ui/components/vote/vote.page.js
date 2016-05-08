import { AutoloadPage } from 'misc/PageLoader';
import * as util from 'misc/Util';

function setVoteState($voteTr, vote) {
  const $voteCount = $voteTr.find('.vote--count');
  $voteCount.text(vote);
}

const votePage = new AutoloadPage(() => {

  $(document).on('click', '.vote', (ev) => {
    const $button = $(ev.currentTarget);
    const $tr = $button.closest('tr');
    const operation = $button.hasClass('vote--upvote') ? 'upvote' : 'downvote';
    const psid = $tr.attr('data-psid');
    util.post($button.closest('form').attr('action'), {
      operation,
      psid,
    })
      .done((data) => {
        setVoteState($tr, data.vote);
      })
      .fail(() => {
        // TODO(iceboy): notify failure
      });
    return false;
  });

});

export default votePage;
