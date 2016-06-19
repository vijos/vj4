import { AutoloadPage } from '../../misc/PageLoader';
import StyledTable from './StyledTable';

const styledTablePage = new AutoloadPage(() => {
  StyledTable.attachAll();
});

export default styledTablePage;
