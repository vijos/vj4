import { AutoloadPage } from '../../misc/PageLoader';
import * as util from '../../misc/Util';
import throttle from 'lodash/throttle';
import Slideout from 'slideout';

let $nav = null;
let $navShadow = null;
let isNavFloating = false;
let isNonTop = false;
let isHover = false;
let isDropdownShow = false;

function floatNav() {
  if (!isNavFloating) {
    $nav.addClass('floating');
    $navShadow.addClass('floating');
    isNavFloating = true;
  }
}

function unfloatNav() {
  if (isNavFloating) {
    $nav.removeClass('floating');
    $navShadow.removeClass('floating');
    isNavFloating = false;
  }
}

function updateNavFloating() {
  if (isNonTop || isHover || isDropdownShow) {
    floatNav();
  } else {
    unfloatNav();
  }
}

function onScroll() {
  if ($(window).scrollTop() > 30) {
    if (!isNonTop) {
      isNonTop = true;
      updateNavFloating();
      $nav.addClass('showlogo');
    }
  } else {
    if (isNonTop) {
      isNonTop = false;
      updateNavFloating();
      $nav.removeClass('showlogo');
    }
  }
}

function onNavEnter() {
  isHover = true;
  updateNavFloating();
}

function onNavLeave() {
  isHover = false;
  updateNavFloating();
}

function onNavDropdownShow() {
  isDropdownShow = true;
  updateNavFloating();
}

function onNavDropdownHide() {
  isDropdownShow = false;
  updateNavFloating();
}

function onNavLogoutClick() {
  const $logoutLink = $('.command--nav-logout');
  util.post($logoutLink.attr('href'))
    .then(() => window.location.reload());
  return false;
}

const navigationPage = new AutoloadPage(() => {
  $nav = $('.nav');
  $navShadow = $('.nav--shadow');

  if ($nav.length > 0
    && document.documentElement.getAttribute('data-layout') === 'basic'
    && window.innerWidth >= 450
  ) {
    $(window).on('scroll', throttle(onScroll, 100));
    $nav.hover(onNavEnter, onNavLeave);
    $nav.on('vjDropdownShow', onNavDropdownShow);
    $nav.on('vjDropdownHide', onNavDropdownHide);
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
