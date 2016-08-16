import { AutoloadPage } from '../../misc/PageLoader';
import Dialog from '../dialog';
import responsiveCutoff from '../../responsive.inc.js';

const signinDialogPage = new AutoloadPage(() => {}, () => {
  const signInDialog = Dialog.getOrConstruct($('.dialog--signin'), {
    cancelByClickingBack: true,
    cancelByEsc: true,
  });

  // don't show quick login dialog if in mobile
  if ($('.command--nav-login').length > 0 && window.innerWidth >= responsiveCutoff.mobile) {
    // nav
    $('.command--nav-login').click((ev) => {
      if (ev.shiftKey || ev.metaKey || ev.ctrlKey) {
        return;
      }
      signInDialog.show();
      ev.preventDefault();
    });
  }

  if ($('.dialog--signin').length > 0) {
    // dialog
    $('.command--dialog--signin__close').on('click', () => {
      signInDialog.hide();
    });
  }
});

export default signinDialogPage;
