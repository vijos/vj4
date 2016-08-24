import _ from 'lodash';
import DOMAttachedObject from '../DOMAttachedObject';

import delay from '../../utils/delay';
import zIndexManager from '../../utils/zIndexManager';

export default class DomDialog extends DOMAttachedObject {

  static DOMAttachKey = 'vjDomDialogInstance';

  constructor($dom, options = {}) {
    super($dom);
    this.isShown = false;
    this.isAnimating = false;
    this.options = {
      cancelByClickingBack: false,
      cancelByEsc: false,
      onAction: () => null,
      ...options,
    };
  }

  async show() {
    if (this.isShown || this.isAnimating) {
      return false;
    }

    this.$dom.css('z-index', zIndexManager.getNext());
    this.$dom.trigger('vjDomDialogShow');
    this.isAnimating = true;

    if (this.options.cancelByClickingBack) {
      this.$dom.on(`click.${this.eventNS}`, this.onClick.bind(this));
    }
    if (this.options.cancelByEsc) {
      $(document).on(`keyup.${this.eventNS}`, this.onKeyUp.bind(this));
    }

    const $wrap = this.$dom;
    $wrap.css({
      display: 'flex',
      opacity: 0,
    });
    $wrap.width();
    $wrap.transition({
      opacity: 1,
    }, {
      duration: 100,
    });

    const $dgContent = this.$dom.find('.dialog__content');
    $dgContent.css({
      scale: 0.8,
    });
    $dgContent.transition({
      scale: 1,
    }, {
      duration: 200,
      easing: 'easeOutCubic',
      complete: () => this.$dom.find('[data-autofocus]').focus(),
    });
    await delay(200);

    this.isShown = true;
    this.isAnimating = false;
    this.$dom.trigger('vjDomDialogShown');

    return true;
  }

  async hide() {
    if (!this.isShown || this.isAnimating) {
      return false;
    }

    this.$dom.trigger('vjDomDialogHide');
    this.isAnimating = true;

    $(document).off(`keyup.${this.eventNS}`);
    this.$dom.off(`click.${this.eventNS}`);

    this.$dom.css({
      opacity: 1,
    });
    this.$dom.transition({
      opacity: 0,
    }, {
      duration: 200,
    });

    const $dgContent = this.$dom.find('.dialog__content');
    $dgContent.css({
      scale: 1,
    });
    $dgContent.transition({
      scale: 0.8,
    }, {
      duration: 200,
      easing: 'easeOutCubic',
      complete: () => this.$dom.css('display', 'none'),
    });
    await delay(200);

    this.isShown = false;
    this.isAnimating = false;
    this.$dom.trigger('vjDomDialogHidden');

    return true;
  }

  action(data) {
    const r = this.options.onAction(data);
    if (r !== false) {
      this.hide();
    }
  }

  onClick(e) {
    if (e.target === this.$dom.get(0)) {
      this.action('cancel');
    }
  }

  onKeyUp(e) {
    if (e.keyCode === 27) {
      this.action('cancel');
    }
  }

}

_.assign(DomDialog, DOMAttachedObject);
