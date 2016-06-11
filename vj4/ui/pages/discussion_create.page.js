import { NamedPage } from 'misc/PageLoader';
import 'simple-cmeditor/dist/simplemde.min.css';

const page = new NamedPage('discussion_create', () => {

  require.ensure([
    'simple-cmeditor/dist/simplemde.min.js',
  ], (require) => {
    const SimpleMDE = require('simple-cmeditor/dist/simplemde.min.js');

    new SimpleMDE({
      element: document.getElementById('markdown-textarea'),
      toolbar: [
        {
          name: 'bold',
          action: SimpleMDE.toggleBold,
          iconClassName: 'icon-bold',
          title: 'Bold',
        },
        {
          name: "italic",
          action: SimpleMDE.toggleItalic,
          iconClassName: 'icon-italic',
          title: 'Italic',
        },
        '|',
        {
          name: 'quote',
          action: SimpleMDE.toggleBlockquote,
          iconClassName: 'icon-quote',
          title: 'Quote',
        },
        {
          name: 'unordered-list',
          action: SimpleMDE.toggleUnorderedList,
          iconClassName: 'icon-unordered_list',
          title: 'Unordered List',
        },
        {
          name: 'ordered-list',
          action: SimpleMDE.toggleOrderedList,
          iconClassName: 'icon-ordered_list',
          title: 'Ordered List',
        },
        '|',
        {
          name: 'link',
          action: SimpleMDE.drawLink,
          iconClassName: 'icon-link',
          title: 'Create Link',
          default: true,
        },
        {
          name: 'image',
          action: SimpleMDE.drawImage,
          iconClassName: 'icon-insert--image',
          title: 'Insert Image',
          default: true,
        },
        '|',
        {
          name: 'preview',
          action: SimpleMDE.togglePreview,
          iconClassName: 'icon-preview',
          className: 'no-disable',
          title: 'Toggle Preview',
          default: true,
        },
        {
          'name': 'guide',
          action: 'https://simplemde.com/markdown-guide',
          iconClassName: "icon-help",
          className: 'no-disable',
          title: 'Markdown Guide',
          default: true,
        },
      ],
      spellChecker: false,
      safe: true,
    });

  });

});

export default page;
