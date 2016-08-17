import _ from 'lodash';
import DOMAttachedObject from '../DOMAttachedObject';

export default class Tab extends DOMAttachedObject {

  static DOMAttachKey = 'vjTabInstance';

  static attachAll() {
    for (const tab of $('.section__tabs')) {
      Tab.getOrConstruct($(tab)).attach();
    }
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

    for (const element of this.$dom.find('.section__tab-title')) {
      $(document.createElement('li')).text($(element).text())
        .addClass('section__tab-header-item')
        .appendTo(this.$header);
    }

    this.$dom.find('.section__tab-main')
      .appendTo(this.$content);

    this.$dom.remove();

    this.selectTab(0);

    return true;
  }

  selectTab(index) {
    this.$header.find('.section__tab-header-item').eq(index).addClass('selected');
  }

}

_.assign(Tab, DOMAttachedObject);
