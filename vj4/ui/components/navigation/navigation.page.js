import { AutoloadPage } from 'misc/PageLoader';
import * as util from 'misc/Util';
import throttle from 'lodash/throttle';

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

function onWindowScroll() {
  if (window.scrollY > 30) {
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
  var $logoutLink = $('.command--nav-logout');
  util.post($logoutLink.attr('href'))
    .then(() => window.location.reload());
  return false;
}

const navigationPage = new AutoloadPage(() => {
  $nav = $('.nav');
  $navShadow = $('.nav--shadow');
  if ($nav.length > 0 && document.documentElement.getAttribute('data-layout') === 'basic') {
    $(window).on('scroll', throttle(onWindowScroll, 100));
    $nav.hover(onNavEnter, onNavLeave);
    $nav.on('vjDropdownShow', onNavDropdownShow);
    $nav.on('vjDropdownHide', onNavDropdownHide);
    $nav.find('.command--nav-logout').click(onNavLogoutClick);
    onWindowScroll();
  }
});

export default navigationPage;
