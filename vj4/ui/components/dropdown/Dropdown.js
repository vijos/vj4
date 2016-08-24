import Drop from 'tether-drop';
import _ from 'lodash';
import DOMAttachedObject from '../DOMAttachedObject';
import responsiveCutoff from '../../responsive.inc.js';

import zIndexManager from '../../utils/zIndexManager';

export default class Dropdown extends DOMAttachedObject {

  static DOMAttachKey = 'vjDropdownInstance';

  static initFromDOM($dom) {
    // special: for navigation bar, show as a menu only in desktop
    if ($dom.attr('data-dropdown-trigger-desktop-only') !== undefined) {
      if (window.innerWidth < responsiveCutoff.mobile) {
        return null;
      }
    }
    const options = {
      target: $.find($dom.attr('data-dropdown-target'))[0],
    };
    if ($dom.attr('data-dropdown-pos')) {
      options.position = $dom.attr('data-dropdown-pos');
    }
    return Dropdown.getOrConstruct($dom, options);
  }

  static initAll() {
    for (const dom of $('[data-dropdown-target]')) {
      Dropdown.initFromDOM($(dom));
    }
  }

  constructor($trigger, options = {}) {
    super($trigger);
    this.options = {
      target: null,
      position: 'bottom left',
      ...options,
    };
    this.dropInstance = new Drop({
      target: $trigger[0],
      classes: 'dropdown',
      content: this.options.target,
      position: this.options.position,
      openOn: 'hover',
      constrainToWindow: true,
      constrainToScrollParent: false,
    });
    this.dropInstance.on('open', this.onDropOpen.bind(this));
    this.dropInstance.on('close', this.onDropClose.bind(this));
  }

  onDropOpen() {
    $(this.dropInstance.drop).css('z-index', zIndexManager.getNext());
    this.$dom.trigger('vjDropdownShow');
  }

  onDropClose() {
    this.$dom.trigger('vjDropdownHide');
  }

}

_.assign(Dropdown, DOMAttachedObject);
