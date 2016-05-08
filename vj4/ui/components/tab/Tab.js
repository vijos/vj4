import assign from 'lodash/assign';
import DOMAttachedObject from 'components/DOMAttachedObject';

export default class Tab extends DOMAttachedObject {

  static attachAll() {
    $('.section__tabs').each((index, table) => Tab.getOrConstruct($(table)).attach());
  }

  constructor($dom) {
    super($dom);
    this.attached = false;
  }

  attach() {
    if (this.attached) {
      return false;
    }

    this.$container = this.$dom.closest('.section__tab-container');

    this.$header = $(document.createElement('ul')).addClass('section__tab-header clearfix');
    this.$content = $(document.createElement('div')).addClass('section__tab-content');

    this.$container
      .append(this.$header)
      .append(this.$content);

    this.$dom.find('.section__tab-title').each((idx, elem) => {
      $(document.createElement('li')).text($(elem).text())
        .addClass('section__tab-header-item')
        .appendTo(this.$header);
    });

    this.$dom.find('.section__tab-main')
      .appendTo(this.$content);

    this.$dom.remove();

    this.selectTab(0);

  }

  selectTab(index) {
    this.$header.find('.section__tab-header-item').eq(index).addClass('selected');
  }

  detach() {
    throw new Error('Not implemented');
  }

}

Tab._attachKey = 'vjTabInstance';
assign(Tab, DOMAttachedObject);
