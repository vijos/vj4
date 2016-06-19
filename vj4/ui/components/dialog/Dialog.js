import assign from 'lodash/assign';
import DOMAttachedObject from '../DOMAttachedObject';

export default class Dialog extends DOMAttachedObject {

  constructor($dom, options = null) {
    super($dom);
    this.dialogShown = false;
    this.options = options;
  }

  show() {
    if (this.dialogShown) {
      return false;
    }

    this.dialogShown = true;
    if (this.options && this.options.cancelByClickingBack) {
      this.$dom.on(`click.${this.eventNS}`, this.onClick.bind(this));
    }
    if (this.options && this.options.cancelByEsc) {
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

    return true;
  }

  hide() {
    if (!this.dialogShown) {
      return false;
    }

    this.dialogShown = false;
    $(document).off(`keyup.${this.eventNS}`);
    this.$dom.off(`click.${this.eventNS}`);
    this.$dom.css({
      opacity: 1,
    });
    this.$dom.transition({
      opacity: 0,
    }, {
      duration: 200,
      complete: () => this.$dom.css('display', 'none'),
    });

    return true;
  }

  onClick(e) {
    if (e.target === this.$dom.get(0)) {
      this.hide();
    }
  }

  onKeyUp(e) {
    if (e.keyCode === 27) {
      this.hide();
    }
  }

}

Dialog.DOMAttachKey = 'vjDialogInstance';
assign(Dialog, DOMAttachedObject);
