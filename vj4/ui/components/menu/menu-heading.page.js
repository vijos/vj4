import { AutoloadPage } from '../../misc/PageLoader';

const menuHeadingPage = new AutoloadPage(null, () => {
  for (const container of $('[data-heading-extract-to]')) {
    const $container = $(container);
    const $target = $('body').find($container.attr('data-heading-extract-to'));
    if ($target.length === 0) {
      continue;
    }
    let $menu = $target.children('.menu');
    if ($menu.length === 0) {
      $menu = $('<ul>').addClass('menu collapsed').appendTo($target);
      $target.children('.menu__link').addClass('expandable');
    }
    for (const heading of $container.find('[data-heading]')) {
      const $heading = $(heading);
      const $a = $('<a>')
        .addClass('menu__link')
        .text($heading.text())
        .attr('href', `#${$heading.attr('id') || 0}`);
      $('<li>')
        .addClass('menu__item')
        .append($a)
        .appendTo($menu);
    }
  }
});

export default menuHeadingPage;
