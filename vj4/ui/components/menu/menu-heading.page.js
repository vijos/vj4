import { AutoloadPage } from '../../misc/PageLoader';

import tpl from '../../utils/tpl';

const menuHeadingPage = new AutoloadPage(null, () => {
  for (const container of $('[data-heading-extract-to]')) {
    const $container = $(container);
    const $target = $('body').find($container.attr('data-heading-extract-to'));
    if ($target.length === 0) {
      continue;
    }
    let $menu = $target.children('.menu');
    if ($menu.length === 0) {
      $menu = $(tpl`<ul class="menu collapsed"></ul>`).appendTo($target);
      $target.children('.menu__link').addClass('expandable');
    }
    for (const heading of $container.find('[data-heading]')) {
      const $heading = $(heading);
      $(tpl`
        <li class="menu__item">
          <a class="menu__link" href="#${$heading.attr('id') || ''}">
            ${$heading.text()}
          </a>
        </li>
      `).appendTo($menu);
    }
  }
});

export default menuHeadingPage;
