import { AutoloadPage } from '../../misc/PageLoader';
import Dropdown from './Dropdown';

const dropdownPage = new AutoloadPage(() => {
  Dropdown.initAll();
});

export default dropdownPage;
