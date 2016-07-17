import _ from 'lodash';
import DOMAttachedObject from '../DOMAttachedObject';

export default class StyledTable extends DOMAttachedObject {

  static attachAll() {
    $('.section__table').each((index, table) => StyledTable.getOrConstruct($(table)).attach());
  }

  constructor($dom) {
    super($dom);
    this.attached = false;
  }

  attach() {
    if (this.attached) {
      return false;
    }

    this.$container = $(document.createElement('div')).addClass('section__table-container');
    this.$container.insertBefore(this.$dom);

    this.$header = $(document.createElement('table'));
    this.$header.attr('class', `${this.$dom.attr('class')} section__table-header`);

    this.$container
      .append(this.$header)
      .append(this.$dom);

    this.update();
    return true;
  }

  update() {
    this.$header.empty();
    this.$dom.children('colgroup').clone().appendTo(this.$header);
    this.$dom.children('thead').appendTo(this.$header);
  }

  detach() {
    throw new Error('Not implemented');
  }

}

StyledTable.DOMAttachKey = 'vjStyledTableInstance';
_.assign(StyledTable, DOMAttachedObject);
