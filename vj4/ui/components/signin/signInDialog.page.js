import { AutoloadPage } from 'vj/misc/PageLoader';
import DomDialog from 'vj/components/dialog/DomDialog';
import responsiveCutoff from 'vj/breakpoints.json';
import { isAbove } from 'vj/utils/mediaQuery';

const signinDialogPage = new AutoloadPage('signinDialogPage', null, () => {
  const signInDialog = DomDialog.getOrConstruct($('.dialog--signin'), {
    cancelByClickingBack: true,
    cancelByEsc: true,
  });

  // don't show quick login dialog if in mobile
  if ($('[name="nav_login"]').length > 0 && isAbove(responsiveCutoff.mobile)) {
    // nav
    $('[name="nav_login"]').click((ev) => {
      if (ev.shiftKey || ev.metaKey || ev.ctrlKey) {
        return;
      }
      signInDialog.show();
      ev.preventDefault();
    });
  }

  if ($('.dialog--signin').length > 0) {
    // dialog
    $('[name="dialog--signin__close"]').on('click', () => {
      signInDialog.hide();
    });
  }

  window.showSignInDialog = () => {
    signInDialog.show();
  };
});

export default signinDialogPage;
