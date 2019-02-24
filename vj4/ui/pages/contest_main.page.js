import { NamedPage } from 'vj/misc/PageLoader';
import Calendar from 'vj/components/calendar';
import i18n from 'vj/utils/i18n';
import { parse as parseMongoId } from 'vj/utils/mongoId';

const page = new NamedPage('contest_main', () => {
  // Contest Filter
  $('[name="filter-form"] [name="rule"]').change(() => {
    $('[name="filter-form"]').submit();
  });
});

export default page;
