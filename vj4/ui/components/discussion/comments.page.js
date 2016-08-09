import { AutoloadPage } from '../../misc/PageLoader';
import CommentBox from '../discussion/CommentBox';
import delay from '../../utils/delay';

const $replyTemplate = $('.commentbox-container').eq(0).clone();

function createReplyContainer($parent) {
  const $container = $replyTemplate
    .clone()
    .hide()
    .prependTo($parent.find('.commentbox-reply-target').eq(0))
    .trigger('vjContentNew');
  return $container.find('.commentbox-placeholder');
}

async function showReplyContainer($parent) {
  const $container = $parent.find('.commentbox-container');
  $container.css({
    position: 'absolute',
    visibility: 'none',
    display: 'block',
  });
  const targetHeight = $container.outerHeight();
  $container.removeAttr('style');
  $container.css({
    opacity: 0,
    height: 0,
    overflow: 'hidden',
  });
  $container.height();

  $container.transition({
    height: targetHeight,
  }, {
    duration: 300,
    easing: 'easeOutCubic',
  });
  await delay(300);

  $container.transition({
    opacity: 1,
  }, {
    duration: 200,
  });
  await delay(200);

  $container.removeAttr('style');
}

async function destroyReplyContainer($parent) {
  const $container = $parent.find('.commentbox-container');
  $container.css({
    height: $container.outerHeight(),
    overflow: 'hidden',
    opacity: 1,
  });

  $container.transition({
    opacity: 0,
  }, {
    duration: 200,
  });
  await delay(200);

  $container.transition({
    height: 0,
  }, {
    duration: 300,
    easing: 'easeOutCubic',
  });
  await delay(300);

  $container.remove();
}

async function onCommentClickReplyComment(ev, options = {}) {
  const $evTarget = $(ev.currentTarget);

  if (CommentBox.get($evTarget)) {
    // If comment box is already expanded,
    // we should insert "initialText"
    CommentBox
      .get($evTarget)
      .insertText(options.initialText || '')
      .focus();
    return;
  }

  const $mediaBody = $evTarget.closest('.media__body');

  const opt = {
    initialText: '',
    mode: 'reply',
    ...options,
    onCancel: async () => {
      await destroyReplyContainer($mediaBody);
    },
  };

  const cbox = CommentBox
    .getOrConstruct($evTarget, {
      form: JSON.parse($evTarget.attr('data-form')),
      ...opt,
    })
    .appendTo(createReplyContainer($mediaBody));
  await showReplyContainer($mediaBody);
  cbox.focus();
}

async function onCommentClickReplyReply(ev) {
  const $evTarget = $(ev.currentTarget);
  const $mediaBody = $evTarget.closest('.media__body');
  const username = $mediaBody
    .find('.user-profile-name').eq(0)
    .text();

  $evTarget
    .closest('.dczcomments__item')
    .find('.dczcomments__op-reply-comment').eq(0)
    .trigger('click', { initialText: `@${username}: ` });
}

async function onCommentClickEdit(ev) {
  const $evTarget = $(ev.currentTarget);

  if (CommentBox.get($evTarget)) {
    CommentBox
      .get($evTarget)
      .focus();
    return;
  }

  const $mediaBody = $evTarget.closest('.media__body');

  const opt = {
    // TODO: retrive original markdown
    initialText: $mediaBody.find('.typo').eq(0)
                           .text()
                           .trim(),
    form: JSON.parse($evTarget.attr('data-form')),
    mode: 'update',
    onCancel: () => {
      $mediaBody.removeClass('is-editing');
    },
  };

  $mediaBody.addClass('is-editing');

  CommentBox
    .getOrConstruct($evTarget, opt)
    .appendTo($mediaBody.find('.commentbox-edit-target').eq(0))
    .focus();
}

function onCommentClickDelete(ev) {
  const $evTarget = $(ev.currentTarget);

  if (CommentBox.get($evTarget)) {
    return;
  }

  const $mediaBody = $evTarget.closest('.media__body');

  const opt = {
    initialText: '',
    form: JSON.parse($evTarget.attr('data-form')),
    mode: 'delete',
    noTextarea: true,
  };

  CommentBox
    .getOrConstruct($evTarget, opt)
    .appendTo($mediaBody.find('.commentbox-edit-target').eq(0))
    .focus();
}

function onClickDummyBox(ev) {
  const $evTarget = $(ev.currentTarget);

  if (CommentBox.get($evTarget)) {
    CommentBox
      .get($evTarget)
      .focus();
    return;
  }

  const $mediaBody = $evTarget.closest('.media__body');

  const opt = {
    form: JSON.parse($evTarget.attr('data-form')),
    mode: 'comment',
    onCancel: () => {
      $mediaBody.removeClass('is-editing');
    },
  };

  $mediaBody.addClass('is-editing');

  CommentBox
    .getOrConstruct($evTarget, opt)
    .appendTo($mediaBody.find('.commentbox-placeholder').eq(0))
    .focus();
}

const commentsPage = new AutoloadPage(() => {
  $(document).on('click', '.dczcomments__dummy-box', onClickDummyBox);
  $(document).on('click', '.dczcomments__op-reply-comment', onCommentClickReplyComment);
  $(document).on('click', '.dczcomments__op-reply-reply', onCommentClickReplyReply);
  $(document).on('click', '.dczcomments__op-edit', onCommentClickEdit);
  $(document).on('click', '.dczcomments__op-delete', onCommentClickDelete);
});

export default commentsPage;
