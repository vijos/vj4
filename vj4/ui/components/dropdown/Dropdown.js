import Drop from 'tether-drop';
import assign from 'lodash/assign';
import DOMAttachedObject from '../DOMAttachedObject';

export default class Dropdown extends DOMAttachedObject {

  static initFromDOM($dom) {
    // special: for navigation bar, show as a menu only in desktop
    if ($dom.attr('data-dropdown-trigger-desktop-only') !== undefined) {
      if (window.innerWidth < 450) {
        return null;
      }
    }
    const options = {
      target: $.find($dom.attr('data-dropdown-target'))[0],
      position: $dom.attr('data-dropdown-position') || 'top left',
    };
    return Dropdown.getOrConstruct($dom, options);
  }

  static initAll() {
    $('.dropdown-trigger').each((index, dom) => Dropdown.initFromDOM($(dom)));
  }

  constructor($trigger, options = {}) {
    super($trigger);
    this.dropInstance = new Drop({
      target: $trigger[0],
      content: options.target,
      position: options.position,
      openOn: 'hover',
      constrainToWindow: true,
      constrainToScrollParent: false,
    });
    this.dropInstance.on('open', this.onDropOpen.bind(this));
    this.dropInstance.on('close', this.onDropClose.bind(this));
  }

  onDropOpen() {
    this.$dom.trigger('vjDropdownShow');
  }

  onDropClose() {
    this.$dom.trigger('vjDropdownHide');
  }

}

Dropdown.DOMAttachKey = 'vjDropdownInstance';
assign(Dropdown, DOMAttachedObject);
