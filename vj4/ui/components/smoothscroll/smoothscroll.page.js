import { AutoloadPage } from '../../misc/PageLoader';
import 'jquery.easing';

const smoothScrollPage = new AutoloadPage(() => {
  $(document).on('click', 'a[href*="#"]', ev => {
    const $target = $(ev.currentTarget.hash);
    if ($target.length === 0) {
      return;
    }
    if (ev.metaKey || ev.ctrlKey || ev.shiftKey) {
      return;
    }
    ev.preventDefault();
    let navHeight = 10;
    const $nav = $('.nav');
    if ($nav.length > 0) {
      navHeight += $nav.height();
    }
    const scrollTop = Math.min(
      $target.offset().top - navHeight,
      document.body.clientHeight - window.innerHeight
    );
    $('html,body').animate({ scrollTop }, 200, 'easeOutCubic');
  });
});

export default smoothScrollPage;
