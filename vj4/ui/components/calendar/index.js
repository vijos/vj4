import _ from 'lodash';
import moment from 'moment';
import tpl from 'vj/utils/tpl';

export default class Calendar {
  constructor(events) {
    this.$dom = $(tpl`
      <div class="calendar">
        <div class="calendar__header">
          <button name="prev"><span class="icon icon-chevron_left"></span></button>
          <h1 class="calendar__header__title"></h1>
          <button name="next"><span class="icon icon-chevron_right"></span></button>
        </div>
        <div class="calendar__week-title">
          <table>
            <thead><tr>
              <th>SUN</th>
              <th>MON</th>
              <th>TUE</th>
              <th>WED</th>
              <th>THU</th>
              <th>FRI</th>
              <th>SAT</th>
            </tr></thead>
          </table>
        </div>
        <div class="calendar__body"></div>
      </div>
    `);
    this.events = events.map(ev => ({
      ...ev,
      beginAt: moment(ev.beginAt),
      endAt: moment(ev.endAt),
    }));
    this.$dom.find('[name="prev"]').click(() => this.navToPrev());
    this.$dom.find('[name="next"]').click(() => this.navToNext());
    this.navToToday();
  }

  navToToday() {
    this.current = moment().date(1);
    this.update();
  }

  navToNext() {
    this.current.add('months', 1);
    this.update();
  }

  navToPrev() {
    this.current.subtract('months', 1);
    this.update();
  }

  update() {
    this.updateHeader();
    this.updateBody();
  }

  updateHeader() {
    this.$dom.find('.calendar__header__title').text(this.current.format('MMMM YYYY'));
  }

  updateBody() {
    const data = this.buildBodyData();
    const $body = this.$dom.find('.calendar__body').empty();
    data.forEach((week) => {
      const $row = $(tpl`<div class="calendar__row">
        <div class="calendar__row__bg"><table><tbody><tr></tr></tbody></table></div>
        <div class="calendar__row__content"><table><thead><tr></tr></thead><tbody></tbody></table></div>
      </div>`);
      const $bgContainer = $row.find('.calendar__row__bg tr');
      const $numContainer = $row.find('.calendar__row__content thead tr');
      const $bannerContainer = $row.find('.calendar__row__content tbody');
      week.days.forEach((day) => {
        const isInactive = day.active ? '' : 'is-inactive';
        const isCurrentDay = day.current ? 'is-current-day' : '';
        const today = day.current ? ' (TODAY)' : '';
        $bgContainer.append($('<td></td>').addClass(isInactive).addClass(isCurrentDay));
        $numContainer.append($(tpl`<th>${day.date.format('D')}${today}</th>`).addClass(isInactive).addClass(isCurrentDay));
      });
      week.banners.forEach((banners) => {
        const $tr = $('<tr/>');
        banners.forEach((banner) => {
          if (banner === undefined) {
            $tr.append('<td></td>');
            return;
          }
          const $cell = $(tpl`<td colspan="${banner.span}"></td>`);
          const $banner = $(tpl`
            <a
              href="${banner.banner.event.link}"
              class="calendar__banner color-${banner.banner.event.colorIndex}"
            >${banner.banner.event.title}</a>
          `);
          if (banner.banner.beginTrunc) {
            $banner.addClass('is-trunc-begin');
          }
          if (banner.banner.endTrunc) {
            $banner.addClass('is-trunc-end');
          }
          $cell.append($banner);
          $tr.append($cell);
        });
        $bannerContainer.append($tr);
      });
      $body.append($row);
    });
  }

  buildBodyData() {
    const now = moment();
    const days = [];
    {
      // back fill
      const base = this.current.clone();
      const dayOfWeek = base.day();
      if (dayOfWeek > 0) {
        base.subtract(dayOfWeek + 1, 'days');
        for (let i = dayOfWeek; i > 0; --i) {
          days.push({
            active: false,
            date: base.add(1, 'days').clone(),
          });
        }
      }
    }
    {
      // current month
      const base = this.current.clone();
      while (base.month() === this.current.month()) {
        days.push({
          active: true,
          date: base.clone(),
        });
        base.add(1, 'days');
      }
    }
    {
      // forward fill
      const base = this.current.clone().add(1, 'months').subtract(1, 'days');
      const dayOfWeek = base.day();
      if (dayOfWeek < 6) {
        for (let i = dayOfWeek; i < 6; ++i) {
          days.push({
            active: false,
            date: base.add(1, 'days').clone(),
          });
        }
      }
    }

    days.forEach((day) => {
      day.current = day.date.isSame(now, 'day'); // eslint-disable-line no-param-reassign
    });

    const numberOfWeeks = days.length / 7;
    const bannersByWeek = _.fill(new Array(numberOfWeeks), 1).map(() => []);
    const beginDate = days[0].date.clone();
    const endDate = _.last(days).date.clone();

    // cut events by week to banners
    this.events.forEach((ev) => {
      if (ev.endAt.isBefore(ev.beginAt, 'day')) {
        return;
      }
      if (ev.endAt.isBefore(beginDate, 'day') || ev.beginAt.isAfter(endDate, 'day')) {
        return;
      }
      let [bannerBegin, bannerBeginTruncated] = [ev.beginAt.clone(), false];
      if (bannerBegin.isBefore(beginDate, 'day')) {
        [bannerBegin, bannerBeginTruncated] = [beginDate.clone(), true];
      }
      do {
        const bannerEndMax = bannerBegin.clone().endOf('week');
        let [bannerEnd, bannerEndTruncated] = [ev.endAt.clone(), false];
        if (bannerEnd.isAfter(bannerEndMax, 'day')) {
          [bannerEnd, bannerEndTruncated] = [bannerEndMax, true];
        }
        const weekIndex = bannerBegin.diff(beginDate, 'week');
        bannersByWeek[weekIndex].push({
          beginAt: bannerBegin.startOf('day'),
          beginTrunc: bannerBeginTruncated,
          endAt: bannerEnd.endOf('day'),
          endTrunc: bannerEndTruncated,
          event: ev,
        });
        if (!bannerEndTruncated) {
          break;
        }
        [bannerBegin, bannerBeginTruncated] = [bannerEnd.clone().add(1, 'day'), true];
      } while (!bannerBegin.isAfter(endDate, 'day'));
    });

    // layout banners
    const layout = bannersByWeek
      .map(banners => _
        .sortBy(banners, [
          banner => banner.beginAt.valueOf(),
          banner => (banner.beginTrunc ? 0 : 1), // truncated events first
          banner => -banner.endAt.valueOf(), // long events first
        ])
      )
      .map((banners) => {
        const dayBitmap = _
          .fill(new Array(7), 1)
          .map(() => []);
        banners.forEach((banner) => {
          const beginDay = banner.beginAt.day();
          const endDay = banner.endAt.day();
          // find available space
          const vIndexMax = _.max(_
            .range(beginDay, endDay + 1)
            .map(day => dayBitmap[day].length)
          );
          let vIndex = 0;
          for (; vIndex < vIndexMax; ++vIndex) {
            if (_.every(_
              .range(beginDay, endDay + 1)
              .map(day => dayBitmap[day][vIndex] === undefined) // eslint-disable-line no-loop-func
            )) {
              break;
            }
          }
          // fill space
          for (let i = beginDay; i <= endDay; ++i) {
            dayBitmap[i][vIndex] = banner;
          }
        });
        // merge adjacent cells and arrange banners by vertical index. only banner cells are merged.
        const vMaxLength = _.max(_.range(0, 7).map(day => dayBitmap[day].length));
        const weekBanners = _
          .fill(new Array(vMaxLength), 1)
          .map(() => []);
        for (let vIndex = 0; vIndex < vMaxLength; ++vIndex) {
          for (let day = 0; day < 7; ++day) {
            const banner = dayBitmap[day][vIndex];
            if (banner === undefined) {
              weekBanners[vIndex].push(undefined);
            } else {
              const last = _.last(weekBanners[vIndex]);
              if (day === 0 || last === undefined || banner !== last.banner) {
                weekBanners[vIndex].push({ span: 1, banner });
              } else {
                _.last(weekBanners[vIndex]).span++;
              }
            }
          }
        }
        return weekBanners;
      });
    return _
      .chunk(days, 7)
      .map((daysInWeek, weekIndex) => ({
        days: daysInWeek,
        banners: layout[weekIndex],
      }));
  }
}
