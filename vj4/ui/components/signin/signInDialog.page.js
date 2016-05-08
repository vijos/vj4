import { AutoloadPage } from 'misc/PageLoader';
import Dialog from 'components/dialog/Dialog';

const signinDialogPage = new AutoloadPage(() => {}, () => {

  const signInDialog = Dialog.getOrConstruct($('.dialog--signin'), {
    cancelByClickingBack: true,
    cancelByEsc: true,
  });

  if ($('.command--nav-login').length > 0) {
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
