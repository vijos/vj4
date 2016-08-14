import _ from 'lodash';
import SimpleMDE from 'vj-simplemde';
import commonmark from 'commonmark';

import 'codemirror/mode/clike/clike';
import 'codemirror/mode/pascal/pascal';
import 'codemirror/mode/python/python';

export default class VjCmEditor extends SimpleMDE {
  constructor(options = {}) {
    const defaultOptions = {
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
          className: 'icon icon-preview no-disable',
          title: 'Toggle Preview',
          default: true,
        },
      ],
      commonmark: {
        safe: true,
      },
    };
    super(_.assign({}, defaultOptions, options));
  }

  markdown(text) {
    const reader = new commonmark.Parser();
    const writer = new commonmark.HtmlRenderer(this.options.commonmark);
    const parsed = reader.parse(text);
    return writer.render(parsed);
  }

}
