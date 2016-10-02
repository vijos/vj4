import { NamedPage } from '../misc/PageLoader';

const page = new NamedPage('contest_main', () => {
  $('[name="filter-form"] [name="rule"]').change(() => {
    $('[name="filter-form"]').submit();
  });
});

export default page;
