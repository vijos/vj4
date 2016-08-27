import _ from 'lodash';
import SimpleMDE from 'vj-simplemde';
import * as util from '../../misc/Util';

import 'codemirror/mode/clike/clike';
import 'codemirror/mode/pascal/pascal';
import 'codemirror/mode/python/python';

export default class VjCmEditor extends SimpleMDE {
  constructor(options = {}) {
    super({
      autoDownloadFontAwesome: false,
      spellChecker: false,
      forceSync: true,
      toolbar: [
        {
          name: 'bold',
          action: SimpleMDE.toggleBold,
          className: 'icon icon-bold',
          title: 'Bold',
        },
        {
          name: 'italic',
          action: SimpleMDE.toggleItalic,
          className: 'icon icon-italic',
          title: 'Italic',
        },
        '|',
        {
          name: 'quote',
          action: SimpleMDE.toggleBlockquote,
          className: 'icon icon-quote',
          title: 'Quote',
        },
        {
          name: 'unordered-list',
          action: SimpleMDE.toggleUnorderedList,
          className: 'icon icon-unordered_list',
          title: 'Unordered List',
        },
        {
          name: 'ordered-list',
          action: SimpleMDE.toggleOrderedList,
          className: 'icon icon-ordered_list',
          title: 'Ordered List',
        },
        '|',
        {
          name: 'link',
          action: SimpleMDE.drawLink,
          className: 'icon icon-link',
          title: 'Create Link',
          default: true,
        },
        {
          name: 'image',
          action: SimpleMDE.drawImage,
          className: 'icon icon-insert--image',
          title: 'Insert Image',
          default: true,
        },
        '|',
        {
          name: 'preview',
          action: SimpleMDE.togglePreview,
          preAction: SimpleMDE.preRenderPreview,
          className: 'icon icon-preview no-disable',
          title: 'Toggle Preview',
          default: true,
        },
      ],
      commonmark: {
        safe: true,
      },
      ...options,
    });
  }

  async markdown(text) {
    const data = await util.ajax({
      url: '/preview',
      method: 'post',
      data: $.param({ text }, true),
    });
    _.defer(this.preparePreview.bind(this));
    return data.html;
  }

  preparePreview() {
    const $preview = $(this.wrapper).find('.simplemde-preview');
    $preview.addClass('typo');
    $preview.attr('data-emoji-enabled', 'true');
    $preview.trigger('vjContentNew');
  }

}
