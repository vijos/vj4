import { AutoloadPage } from '../../misc/PageLoader';
import * as util from '../../misc/Util';
import _ from 'lodash';
import Slideout from 'slideout';
import nav from './navigation.js';

const $nav = nav.$nav;

function onScroll() {
  if ($(window).scrollTop() > 30) {
    if (!nav.state.nonTop) {
      nav.setState('nonTop', true);
      $nav.addClass('showlogo');
    }
  } else {
    if (nav.state.nonTop) {
      nav.setState('nonTop', false);
      $nav.removeClass('showlogo');
    }
  }
}

function onNavLogoutClick() {
  const $logoutLink = $('.command--nav-logout');
  util.post($logoutLink.attr('href'))
    .then(() => window.location.reload());
  return false;
}

const navigationPage = new AutoloadPage(() => {
  if ($nav.length > 0
    && document.documentElement.getAttribute('data-layout') === 'basic'
    && window.innerWidth >= 450
  ) {
    $(window).on('scroll', _.throttle(onScroll, 100));
    $nav.hover(
      () => nav.setState('hover', true),
      () => nav.setState('hover', false)
    );
    $nav.on('vjDropdownShow', () => nav.setState('dropdown', true));
    $nav.on('vjDropdownHide', () => nav.setState('dropdown', false));
    onScroll();
  }

  $nav.find('.command--nav-logout').click(onNavLogoutClick);

  const slideout = new Slideout({
    panel: document.getElementById('panel'),
    menu: document.getElementById('menu'),
    padding: 256,
    tolerance: 70,
  });
  [['beforeopen', 'add'], ['beforeclose', 'remove']].forEach(([event, action]) => {
    slideout.on(event, () => $('.nav__hamburger .hamburger')[`${action}Class`]('is-active'));
  });

  $('.nav__hamburger').click(() => slideout.toggle());
});

export default navigationPage;
