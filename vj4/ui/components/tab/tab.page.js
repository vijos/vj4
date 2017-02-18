import { AutoloadPage } from 'vj/misc/PageLoader';
import Tab from './Tab';

const tabPage = new AutoloadPage(() => {
  Tab.attachAll();
});

export default tabPage;
