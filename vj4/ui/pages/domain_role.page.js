import { NamedPage } from '../misc/PageLoader';

import { ActionDialog } from '../components/dialog';

const page = new NamedPage('domain_role', () => {
  const createRoleDialog = new ActionDialog({
    $body: $('.dialog__body--create-role > div'),
    onAction: action => {
      if (action !== 'ok') {
        return true;
      }
      window.location.reload();
      return true;
    },
  });

  function openCreateRoleDialog() {
    createRoleDialog.$dom.find('[name="role"]').val('');
    createRoleDialog.open();
  }

  function handleSelectAllChange(ev) {
    $('.domain-roles tbody input[type="checkbox"]:enabled').prop('checked', $(ev.currentTarget).prop('checked'));
  }

  $('[name="create_role"]').click(() => openCreateRoleDialog());
  $('[name="delete_selected"]').click(() => alert('not implemented'));
  $('.domain-roles [name="select_all"]').change(ev => handleSelectAllChange(ev));
});

export default page;
