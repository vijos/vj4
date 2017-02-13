import _ from 'lodash';
import DOMAttachedObject from '../DOMAttachedObject';

export default class Tab extends DOMAttachedObject {

  static DOMAttachKey = 'vjTabInstance';

  static attachAll() {
    $('.section__tabs').get().forEach((tab) => {
      Tab.getOrConstruct($(tab)).attach();
    });
  }

  constructor($dom) {
    super($dom);
    this.attached = false;
  }

  handleClick(i) {
    return () => this.selectTab(i);
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

    let i = 0;
    this.$dom.find('.section__tab-title').get().forEach((element) => {
      $(document.createElement('li')).text($(element).text())
        .addClass('section__tab-header-item')
        .on('click', this.handleClick(i))
        .appendTo(this.$header);
      ++i;
    });

    this.$dom.find('.section__tab-main')
      .appendTo(this.$content);

    this.$dom.remove();

    this.selectTab(0);

    return true;
  }

  selectTab(index) {
    this.$header.find('.section__tab-header-item').removeClass('selected');
    this.$header.find('.section__tab-header-item').eq(index).addClass('selected');
    this.$content.find('.section__tab-main').css('display', 'none');
    this.$content.find('.section__tab-main').eq(index).css('display', '');
  }

}

_.assign(Tab, DOMAttachedObject);
