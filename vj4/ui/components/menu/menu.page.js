import { AutoloadPage } from '../../misc/PageLoader';
import delay from '../../utils/delay';
import { slideDown } from '../../utils/slide';

async function expandMenu($menu) {
  slideDown($menu, 500, { opacity: 0 }, { opacity: 1});
}

const menuPage = new AutoloadPage(() => {
  for (const menu of $('.menu.collapsed')) {
    expandMenu($(menu));
  }
});

export default menuPage;
