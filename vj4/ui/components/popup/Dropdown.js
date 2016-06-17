import Popup from './Popup';
import assign from 'lodash/assign';
import DOMAttachedObject from '../DOMAttachedObject';

export default class Dropdown extends DOMAttachedObject {

  /**
   * Prepare the object from preferences specified in DOM attributes
   */
  static initFromDOM($dom) {
    const options = {
      expandOnHover: $dom.attr('data-dropdown-hover') === 'true',
      alignRight: $dom.attr('data-dropdown-align') === 'right',
    };
    const popupOptions = {
      position: $dom.attr('data-dropdown-position') || 'absolute',
      anchorVertical: Popup.PopupLayoutAnchor.bottom_outside,
      anchorHorizontal: Popup.PopupLayoutAnchor.left_inside,
    };
    if (options.alignRight) {
      popupOptions.anchorHorizontal = Popup.PopupLayoutAnchor.right_inside;
    }
    const dropdown = Dropdown.getOrConstruct($dom, popupOptions, options);
    if ($dom.attr('data-popup-zindex')) {
      dropdown.$popup.css('z-index', $dom.attr('data-popup-zindex'));
    }
    return dropdown;
  }

  static initAll() {
    $('.dropdown-target').each((index, dom) => Dropdown.initFromDOM($(dom)));
  }

  constructor($target, popupOptions, options = null) {
    super($target);

    this.$popup = $(`#${this.$dom.attr('data-popup-id')}`);
    this.$popup.appendTo(document.body);
    this.popup = Popup.getOrConstruct(this.$popup);
    this.options = options;
    this.popupOptions = popupOptions;
    /**
     * Whether user is hovering on the target
     */
    this.targetHover = false;
    /**
     * The delay timer to hide the popup
     * when user hovers out
     */
    this.popupHideTimer = -1;

    this.attachEventListeners();
  }

  attachEventListeners() {
    this.$popup.on('vjPopupShow', this.onPopupShow.bind(this));
    this.$popup.on('vjPopupHide', this.onPopupHide.bind(this));
    this.$popup.on('click', this.onPopupClick.bind(this));
    if (this.options && this.options.expandOnHover) {
      this.$dom.hover(this.onTargetEnter.bind(this), this.onTargetLeave.bind(this));
      this.$popup.on('vjPopupLeave', this.onPopupLeave.bind(this));
    } else {
      this.$dom.click(this.onTargetClick.bind(this));
    }
  }

  onTargetClick(e) {
    this.popup.show(this.$dom, this.popupOptions);
    e.preventDefault();
    e.stopImmediatePropagation();
  }

  onTargetEnter() {
    this.targetHover = true;
    if (this.options && this.options.expandOnHover) {
      this.popup.show(this.$dom, this.popupOptions);
    }
    if (this.popupHideTimer !== -1) {
      clearTimeout(this.popupHideTimer);
      this.popupHideTimer = -1;
    }
  }

  onTargetLeave() {
    this.targetHover = false;
    if (this.popupHideTimer !== -1) {
      clearTimeout(this.popupHideTimer);
    }
    // Delay the hiding a little
    this.popupHideTimer = setTimeout(() => {
      this.popup.hideIfNotHover();
    }, 100);
  }

  onPopupShow() {
    this.$dom.trigger('vjDropdownShow');
  }

  onPopupHide() {
    this.$dom.trigger('vjDropdownHide');
  }

  onPopupClick(ev) {
    if ($(ev.currentTarget).closest('.menu__item').length > 0) {
      this.popup.hide();
    }
  }

  /**
   * Hide the popup if user leaves the popup.
   */
  onPopupLeave() {
    if (this.options && this.options.expandOnHover && !this.targetHover) {
      this.onTargetLeave();
    }
  }

}

Dropdown.DOMAttachKey = 'vjDropdownInstance';
assign(Dropdown, DOMAttachedObject);
