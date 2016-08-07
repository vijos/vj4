import 'pickadate/lib/picker.date';
import 'pickadate/lib/picker.time';

import { AutoloadPage } from '../../misc/PageLoader';

const datepickerPage = new AutoloadPage(() => {
  $('[data-pick-date]').pickadate({
    format: 'yyyy-m-d',
    clear: false,
  });
  $('[data-pick-time]').pickatime({
    format: 'H:i',
    interval: 15,
    clear: false,
  });
});

export default datepickerPage;
