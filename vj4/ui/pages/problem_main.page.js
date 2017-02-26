import _ from 'lodash';

import { NamedPage } from 'vj/misc/PageLoader';
import Dropdown from 'vj/components/dropdown/Dropdown';
import request from 'vj/utils/request';
import substitute from 'vj/utils/substitute';

const categories = {};
const dirtyCategories = [];
const selections = [];

function setDomSelected($dom, selected) {
  if (selected) {
    $dom.addClass('selected');
  } else {
    $dom.removeClass('selected');
  }
}

async function updateSelection() {
  dirtyCategories.forEach(({ type, category, subcategory }) => {
    let item = categories[category];
    const isSelected = item.select || _.some(item.children, c => c.select);
    setDomSelected(item.$tag, isSelected);
    if (isSelected) {
      selections.push(category);
    } else {
      _.pull(selections, category);
    }
    if (type === 'subcategory') {
      item = categories[category].children[subcategory];
      setDomSelected(item.$tag, item.select);
      const selectionName = `${category} ${subcategory}`;
      if (item.select) {
        selections.push(selectionName);
      } else {
        _.pull(selections, selectionName);
      }
    }
  });
  dirtyCategories.length = 0;

  // make request according to the selection
  const requestTags = _.uniq(_.flatten(selections.map(s => s.split(' '))));
  const resp = await request.get(substitute(decodeURIComponent(Context.getProblemUrl), {
    category: requestTags.map(tag => encodeURIComponent(tag)).join('+'),
  }));
  console.log(resp);
}

function buildCategoryFilter() {
  const $container = $('[data-widget-cf-container]');
  if (!$container) {
    return;
  }
  $container.attr('class', 'widget--category-filter row small-up-3 medium-up-2');
  $container.children('li').get().forEach((category) => {
    const $category = $(category)
      .attr('class', 'widget--category-filter__category column');
    const $categoryTag = $category
      .find('.section__title a')
      .remove()
      .attr('onclick', 'return false')
      .attr('class', 'widget--category-filter__category-tag');
    const categoryText = $categoryTag.text();
    const $drop = $category
      .children('.chip-list')
      .remove()
      .attr('class', 'widget--category-filter__drop');
    const treeItem = {
      select: false,
      $tag: $categoryTag,
      children: {},
    };
    categories[categoryText] = treeItem;
    $category.empty().append($categoryTag);
    if ($drop.length > 0) {
      $categoryTag.text(`${$categoryTag.text()}`);
      const $subCategoryTags = $drop
        .children('li')
        .attr('class', 'widget--category-filter__subcategory')
        .find('a')
        .attr('onclick', 'return false')
        .attr('class', 'widget--category-filter__subcategory-tag')
        .attr('data-category', categoryText);
      $subCategoryTags.get().forEach((subCategoryTag) => {
        const $tag = $(subCategoryTag);
        treeItem.children[$tag.text()] = {
          select: false,
          $tag,
        };
      });
      Dropdown.getOrConstruct($categoryTag, {
        target: $drop[0],
        position: 'left center',
      });
    }
  });
  $(document).on('click', '.widget--category-filter__category-tag', (e) => {
    const category = $(e.currentTarget).text();
    const treeItem = categories[category];
    // the effect should be cancelSelect if it is shown as selected when clicking
    const shouldSelect = treeItem.$tag.hasClass('selected') ? false : !treeItem.select;
    treeItem.select = shouldSelect;
    dirtyCategories.push({ type: 'category', category });
    if (!shouldSelect) {
      // de-select children
      _.forEach(treeItem.children, (treeSubItem, subcategory) => {
        if (treeSubItem.select) {
          treeSubItem.select = false; // eslint-disable-line no-param-reassign
          dirtyCategories.push({ type: 'subcategory', subcategory, category });
        }
      });
    }
    updateSelection();
  });
  $(document).on('click', '.widget--category-filter__subcategory-tag', (e) => {
    const subcategory = $(e.currentTarget).text();
    const category = $(e.currentTarget).attr('data-category');
    const treeItem = categories[category].children[subcategory];
    treeItem.select = !treeItem.select;
    dirtyCategories.push({ type: 'subcategory', subcategory, category });
    updateSelection();
  });
}

const page = new NamedPage(['problem_main', 'problem_category'], () => {
  buildCategoryFilter();
});

export default page;
