import { NamedPage } from '../misc/PageLoader';

const page = new NamedPage('discussion_create', async () => {
  const CMEditor = (await System.import('../components/cmeditor/CMEditor')).default;
  // TODO
  // eslint-disable-next-line no-new
  new CMEditor({
    element: document.getElementById('markdown-textarea'),
  });
});

export default page;
