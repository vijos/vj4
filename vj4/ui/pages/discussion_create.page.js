import { NamedPage } from 'misc/PageLoader';
import 'simple-cmeditor/dist/simplemde.min.css';

const page = new NamedPage('discussion_create', () => {

  require.ensure([
    'components/cmeditor/CMEditor',
  ], (require) => {
    const CMEditor = require('components/cmeditor/CMEditor').default;
    new CMEditor({
      element: document.getElementById('markdown-textarea'),
    });
  });

});

export default page;
