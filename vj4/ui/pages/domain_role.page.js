import { NamedPage } from '../misc/PageLoader';

import { ActionDialog } from '../components/dialog';

import * as util from '../misc/Util';

const page = new NamedPage('domain_role', () => {
  const createRoleDialog = new ActionDialog({
    $body: $('.dialog__body--create-role > div'),
    onAction: async action => {
      if (action !== 'ok') {
        return true;
      }
      const role = createRoleDialog.$dom.find('[name="role"]').val();
      if (role === '') {
        return false;
      }
      await util.post('', {
        operation: 'set',
        role,
      });
      window.location.reload();
      return true;
    },
  });

  function openCreateRoleDialog() {
    createRoleDialog.$dom.find('[name="role"]').val('');
    createRoleDialog.open();
  }

  function handleDeleteSelected() {
    $('.domain-roles tbody input[type="checkbox"]:checked').closest('tr').each((i, e) => {
      alert($(e).attr('data-role'));
    });
  }

  $('[name="create_role"]').click(() => openCreateRoleDialog());
  $('[name="delete_selected"]').click(() => handleDeleteSelected());
});

export default page;
