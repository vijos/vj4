import 'pickadate/lib/picker.date';
import 'pickadate/lib/picker.time';
import 'pickadate/lib/themes/classic.css';
import 'pickadate/lib/themes/classic.date.css';
import 'pickadate/lib/themes/classic.time.css';

import { AutoloadPage } from '../../misc/PageLoader';

const datepickerPage = new AutoloadPage(() => {
  $('[data-pick-date]').pickadate({
    format: 'yyyy-m-d',
  });
  $('[data-pick-time]').pickatime({
    format: 'H:i',
    interval: 15,
    clear: false,
  });
});

export default datepickerPage;
