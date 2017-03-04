import { AutoloadPage } from 'vj/misc/PageLoader';
import Tab from './Tab';

const tabPage = new AutoloadPage('tabPage', () => {
  Tab.initAll();
});

export default tabPage;
