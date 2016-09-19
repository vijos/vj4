import tpl from '../../utils/tpl';
import zIndexManager from '../../utils/zIndexManager';

let lastNotification = null;

export default class Notification {

  static info(message, duration) {
    Notification.show({ type: 'info', message, duration });
  }

  static warn(message, duration) {
    Notification.show({ type: 'warn', message, duration });
  }

  static error(message, duration) {
    Notification.show({ type: 'error', message, duration });
  }

  static show({ message, type, duration }) {
    if (lastNotification) {
      Notification.hide();
    }
    const $n = $(tpl`<div class="notification ${type} hide">${message}</div>`)
      .css('z-index', zIndexManager.getNext())
      .appendTo('body');
    $n.width(); // force reflow
    $n.removeClass('hide');
    lastNotification = $n;
  }

  static hide() {
    if (!lastNotification) {
      return;
    }
    const $n = lastNotification;
    $n.addClass('hide');
    setTimeout(() => $n.remove(), 200);
    lastNotification = null;
  }

}
