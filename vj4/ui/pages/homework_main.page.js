import { NamedPage } from 'vj/misc/PageLoader';
import Calendar from 'vj/components/calendar';

import moment from 'moment';

const page = new NamedPage('homework_main', () => {
  const calendar = new Calendar([
    {
      beginAt: moment('2017-09-27 14:00:00').valueOf(),
      endAt: moment('2017-09-27 18:00:00').valueOf(),
      title: 'Assignment 5',
      colorIndex: 0,
      link: '#',
    },
    {
      beginAt: moment('2017-08-28 14:00:00').valueOf(),
      endAt: moment('2017-09-13 18:00:00').valueOf(),
      title: 'Assignment 1',
      colorIndex: 5,
      link: '#',
    },
    {
      beginAt: moment('2017-09-05 14:00:00').valueOf(),
      endAt: moment('2017-09-08 18:00:00').valueOf(),
      title: 'Assignment 2',
      colorIndex: 8,
      link: '#',
    },
    {
      beginAt: moment('2017-09-26 14:00:00').valueOf(),
      endAt: moment('2017-09-29 18:00:00').valueOf(),
      title: 'Assignment 3',
      colorIndex: 3,
      link: '#',
    },
    {
      beginAt: moment('2017-09-28 14:00:00').valueOf(),
      endAt: moment('2017-10-01 18:00:00').valueOf(),
      title: 'Assignment 7',
      colorIndex: 10,
      link: '#',
    },
    {
      beginAt: moment('2017-09-25 14:00:00').valueOf(),
      endAt: moment('2017-09-27 18:00:00').valueOf(),
      title: 'Assignment 10',
      colorIndex: 12,
      link: '#',
    },
  ]);
  calendar.$dom.appendTo('.section');
});

export default page;
