import { AutoloadPage } from 'vj/misc/PageLoader';
import Dropdown from './Dropdown';

const dropdownPage = new AutoloadPage('dropdownPage', () => {
  Dropdown.initAll();
});

export default dropdownPage;
