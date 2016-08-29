import { AutoloadPage } from '../../misc/PageLoader';
import { slideDown } from '../../utils/slide';
import delay from '../../utils/delay';

function expandMenu($menu) {
  slideDown($menu, 500, { opacity: 0 }, { opacity: 1 });
}

async function expandAllMenus() {
  await delay(200);
  for (const menu of $('.menu.collapsed')) {
    expandMenu($(menu));
  }
}

const menuPage = new AutoloadPage(() => {
  expandAllMenus();
});

export default menuPage;
