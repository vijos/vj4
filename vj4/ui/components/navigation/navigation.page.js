import _ from 'lodash';
import Slideout from 'slideout';

import { AutoloadPage } from 'vj/misc/PageLoader';
import request from 'vj/utils/request';
import responsiveCutoff from 'vj/breakpoints.json';
import Navigation from './navigation.js';

const nav = Navigation.instance;
const $nav = nav.$nav;

function handleScroll() {
  const currentState = $(window).scrollTop() > 20;
  if (nav.floating.get('nonTop') !== currentState) {
    nav.floating.set('nonTop', currentState);
    nav.logoVisible.set('nonTop', currentState);
  }
}

function handleNavLogoutClick(ev) {
  const $logoutLink = $(ev.currentTarget);
  request
    .post($logoutLink.attr('href'))
    .then(() => window.location.reload());
  ev.preventDefault();
}

const navigationPage = new AutoloadPage('navigationPage', () => {
  if (!document.getElementById('panel') || !document.getElementById('menu')) {
    return;
  }
  if ($nav.length > 0
    && document.documentElement.getAttribute('data-layout') === 'basic'
    && window.innerWidth >= responsiveCutoff.mobile
  ) {
    $(window).on('scroll', _.throttle(handleScroll, 100));
    $nav.hover(
      () => nav.floating.set('hover', true),
      () => nav.floating.set('hover', false),
    );
    $nav.on('vjDropdownShow', () => nav.floating.set('dropdown', true));
    $nav.on('vjDropdownHide', () => nav.floating.set('dropdown', false));
    handleScroll();
  }

  $(document).on('click', '[name="nav_logout"]', handleNavLogoutClick);

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
