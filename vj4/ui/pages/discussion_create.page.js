import { NamedPage } from '../misc/PageLoader';

const page = new NamedPage('discussion_create', async () => {
  const { default: CmEditor } = await System.import('../components/cmeditor');
  // TODO
  // eslint-disable-next-line no-new
  new CmEditor({
    element: document.getElementById('markdown-textarea'),
  });
});

export default page;
