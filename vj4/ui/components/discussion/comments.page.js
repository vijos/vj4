import { AutoloadPage } from '../../misc/PageLoader';
import CommentBox from '../discussion/CommentBox';

const $template = $('.commentbox-container').eq(0).clone();

function createCommentBoxContainer($parent) {
  const $container = $template.clone();
  $parent.find('.commentbox-prepend-target').eq(0).prepend($container);
  $container.trigger('vjContentNew');
  return $container.find('.commentbox-placeholder');
}

function destroyCommentBoxContainer($parent) {
  $parent.find('.commentbox-container').remove();
}

function onCommentClickReply(ev, options = {}) {
  const $evTarget = $(ev.currentTarget);

  if (CommentBox.get($evTarget)) {
    CommentBox
      .get($evTarget)
      .insertText(options.initialText || '')
      .focus();
    return;
  }

  const $mediaBody = $evTarget.closest('.media__body');
  const isInReply = $evTarget.closest('.dczcomments__reply').length > 0;

  const opt = {
    initialText: '',
    mode: 'reply',
    ...options,
    onCancel: () => {
      destroyCommentBoxContainer($mediaBody);
    },
  };

  if (isInReply) {
    const username = $mediaBody
      .find('.user-profile-name').eq(0)
      .text();
    $evTarget
      .closest('.dczcomments__item')
      .find('.dczcomments__op-reply').eq(0)
      .trigger('click', { initialText: `@${username}: ` });
  } else {
    CommentBox
      .getOrConstruct($evTarget, {
        form: JSON.parse($evTarget.attr('data-form')),
        ...opt,
      })
      .appendTo(createCommentBoxContainer($mediaBody))
      .focus();
  }
}

function onCommentClickEdit(ev) {
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
    initialText: $mediaBody.find('.typo').text().trim(),
    form: JSON.parse($evTarget.attr('data-form')),
    mode: 'update',
    onCancel: () => {
      destroyCommentBoxContainer($mediaBody);
      $mediaBody.removeClass('is-editing');
    },
  };

  $mediaBody.addClass('is-editing');

  CommentBox
    .getOrConstruct($evTarget, opt)
    .appendTo(createCommentBoxContainer($mediaBody))
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
  $(document).on('click', '.dczcomments__op-reply', onCommentClickReply);
  $(document).on('click', '.dczcomments__op-edit', onCommentClickEdit);
});

export default commentsPage;
