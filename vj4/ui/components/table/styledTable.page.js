import { AutoloadPage } from 'vj/misc/PageLoader';
import StyledTable from './StyledTable';

const styledTablePage = new AutoloadPage(() => {
  StyledTable.attachAll();
});

export default styledTablePage;
