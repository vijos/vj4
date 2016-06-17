/* eslint-disable no-underscore-dangle */
import assign from 'lodash/assign';
import DOMAttachedObject from '../DOMAttachedObject';

export default class Popup extends DOMAttachedObject {

  static PopupLayoutAnchor = {
    left_inside: 0,
    top_inside: 1,
    right_inside: 2,
    bottom_inside: 3,
    left_outside: 4,
    top_outside: 5,
    right_outside: 6,
    bottom_outside: 7,
  }

  constructor($dom) {
    super($dom);

    /**
     * Whether the popup is shown
     */
    this.popupShown = false;

    /**
     * Whether user hovers on the popup
     */
    this.popupHover = false;
  }

  /**
   * Get the coordinates relative to the screen
   * according to the given preference.
   */
  getScreenPosition($target, anchor, position = 'absolute') {
    const popupWidth = this.$dom.outerWidth();
    const popupHeight = this.$dom.outerHeight();
    const targetWidth = $target.outerWidth();
    const targetHeight = $target.outerHeight();
    let basePos;
    if (position === 'absolute') {
      basePos = $target.offset();
      basePos.left -= window.scrollX;
      basePos.top -= window.scrollY;
    } else if (position === 'fixed') {
      basePos = $target.position();
    } else {
      throw new Error('Invalid argument: position');
    }
    switch (anchor) {
    case Popup.PopupLayoutAnchor.left_inside:
      return basePos.left;
    case Popup.PopupLayoutAnchor.top_inside:
      return basePos.top;
    case Popup.PopupLayoutAnchor.right_inside:
      return basePos.left + targetWidth - popupWidth;
    case Popup.PopupLayoutAnchor.bottom_inside:
      return basePos.top + targetHeight - popupHeight;
    case Popup.PopupLayoutAnchor.left_outside:
      return basePos.left - popupWidth;
    case Popup.PopupLayoutAnchor.top_outside:
      return basePos.top - popupHeight;
    case Popup.PopupLayoutAnchor.right_outside:
      return basePos.left + targetWidth;
    case Popup.PopupLayoutAnchor.bottom_outside:
      return basePos.top + targetHeight;
    default:
      throw new Error('Invalid anchor');
    }
  }

  /**
   * Test whether the boundary of the popup
   * is outside the screen.
   */
  isPopupOverflow($target, anchor, position = 'absolute') {
    const popupWidth = this.$dom.outerWidth();
    const popupHeight = this.$dom.outerHeight();
    const pos = this.getScreenPosition($target, anchor, position);
    switch (anchor) {
    case Popup.PopupLayoutAnchor.left_inside:
    case Popup.PopupLayoutAnchor.right_outside:
      return pos + popupWidth > window.innerWidth;
    case Popup.PopupLayoutAnchor.top_inside:
    case Popup.PopupLayoutAnchor.bottom_outside:
      return pos + popupHeight > window.innerHeight;
    case Popup.PopupLayoutAnchor.right_inside:
    case Popup.PopupLayoutAnchor.bottom_inside:
    case Popup.PopupLayoutAnchor.left_outside:
    case Popup.PopupLayoutAnchor.top_outside:
      return pos < 0;
    default:
      throw new Error('Invalid anchor');
    }
  }

  /**
   * Show the popup
   */
  show($target, options) {
    if (this.popupShown) {
      return false;
    }

    // measure size by setting position to absolute
    this.$dom.css('position', options.position);

    this._anchorH = options.anchorHorizontal;
    this._anchorV = options.anchorVertical;

    // whether there are enough space
    switch (this._anchorH) {
    case Popup.PopupLayoutAnchor.left_outside:
      if (this.isPopupOverflow($target, this._anchorH, options.position)) {
        if (!this.isPopupOverflow($target,
          Popup.PopupLayoutAnchor.right_outside,
          options.position
        )) {
          this._anchorH = Popup.PopupLayoutAnchor.right_outside;
        }
      }
      break;
    case Popup.PopupLayoutAnchor.right_outside:
      if (this.isPopupOverflow($target, this._anchorH, options.position)) {
        if (!this.isPopupOverflow($target,
          Popup.PopupLayoutAnchor.left_outside,
          options.position
        )) {
          this._anchorH = Popup.PopupLayoutAnchor.left_outside;
        }
      }
      break;
    default:
      throw new Error('Invalid anchor');
    }
    switch (this._anchorV) {
    case Popup.PopupLayoutAnchor.top_outside:
      if (this.isPopupOverflow($target, this._anchorV, options.position)) {
        if (!this.isPopupOverflow($target,
          Popup.PopupLayoutAnchor.bottom_outside,
          options.position
        )) {
          this._anchorV = Popup.PopupLayoutAnchor.bottom_outside;
        }
      }
      break;
    case Popup.PopupLayoutAnchor.bottom_outside:
      if (this.isPopupOverflow($target, this._anchorV, options.position)) {
        if (!this.isPopupOverflow($target,
          Popup.PopupLayoutAnchor.top_outside,
          options.position
        )) {
          this._anchorV = Popup.PopupLayoutAnchor.top_outside;
        }
      }
      break;
    default:
      throw new Error('Invalid anchor');
    }

    // show popup based on final anchor
    this._$target = $target;
    this._options = options;

    let posX = this.getScreenPosition(this._$target,
      this._anchorH,
      this._options.position
    );
    let posY = this.getScreenPosition(this._$target,
      this._anchorV,
      this._options.position
    );
    if (this._options.position === 'absolute') {
      posX += window.scrollX;
      posY += window.scrollY;
    }

    const success = this.showAtPosition(posX, posY);

    if (success) {
      $(window).on(`resize.${this.eventNS}`, this.onWindowResize.bind(this));
    }

    return success;
  }

  /**
   * Show the popup at the given position
   */
  showAtPosition(x, y, position = null) {
    if (this.popupShown) {
      return false;
    }

    this.popupShown = true;

    if (position !== null) {
      this.$dom.css('position', position);
    }
    this.$dom.css({
      left: x,
      top: y,
      opacity: 0,
      display: 'block',
    });
    this.$dom.width();
    this.$dom.stop();
    this.$dom.transition({
      opacity: 1,
    }, {
      duration: 200,
    });

    this.$dom.mouseenter(this.onMouseEnter.bind(this));
    this.$dom.mouseleave(this.onMouseLeave.bind(this));
    this.$dom.trigger('vjPopupShow');

    return true;
  }

  /**
   * Hide the popup
   */
  hide() {
    if (!this.popupShown) {
      return false;
    }

    this.popupShown = false;
    this.$dom.stop();
    this.$dom.transition({
      opacity: 0,
    }, {
      duration: 200,
      complete: () => {
        if (!this.popupShown) {
          this.$dom.css('display', 'none');
        }
      },
    });

    $(window).off(`resize.${this.eventNS}`);

    this.$dom.off('mouseenter');
    this.$dom.off('mouseleave');
    this.$dom.trigger('vjPopupHide');

    return true;
  }

  /**
   * Hide the popup if user is not hovering on it
   */
  hideIfNotHover() {
    if (!this.popupHover) {
      return this.hide();
    }
    return false;
  }

  /**
   * Adjust popup position when window is resized.
   * Only enabled when calling show(...).
   */
  onWindowResize() {
    let posX = this.getScreenPosition(this._$target,
      this._anchorH,
      this._options.position
    );
    let posY = this.getScreenPosition(this._$target,
      this._anchorV,
      this._options.position
    );

    if (this._options.position === 'absolute') {
      posX += window.scrollX;
      posY += window.scrollY;
    }

    this.$dom.css({
      left: posX,
      top: posY,
    });
  }

  onMouseEnter() {
    this.popupHover = true;
    this.$dom.trigger('vjPopupEnter');
  }

  onMouseLeave() {
    this.popupHover = false;
    this.$dom.trigger('vjPopupLeave');
  }

}

Popup.DOMAttachKey = 'vjPopupInstance';
assign(Popup, DOMAttachedObject);
