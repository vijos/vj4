import { NamedPage } from '../misc/PageLoader';

const page = new NamedPage('discussion_create', async () => {
  const { default: CMEditor } = await System.import('../components/cmeditor');
  // TODO
  // eslint-disable-next-line no-new
  new CMEditor({
    element: document.getElementById('markdown-textarea'),
  });
});

export default page;
