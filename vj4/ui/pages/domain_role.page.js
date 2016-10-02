import _ from 'lodash';

import { NamedPage } from '../misc/PageLoader';
import Notification from '../components/notification';
import { ConfirmDialog, ActionDialog } from '../components/dialog';

import * as util from '../misc/Util';
import tpl from '../utils/tpl';
import delay from '../utils/delay';

const page = new NamedPage('domain_role', () => {
  const createRoleDialog = new ActionDialog({
    $body: $('.dialog__body--create-role > div'),
    onDispatch(action) {
      const $role = createRoleDialog.$dom.find('[name="role"]');
      if (action === 'ok' && $role.val() === '') {
        $role.focus();
        return false;
      }
      return true;
    },
  });
  createRoleDialog.clear = function () {
    this.$dom.find('[name="role"]').val('');
    return this;
  };

  function ensureAndGetSelectedRoles() {
    const roles = _.map(
      $('.domain-roles tbody [type="checkbox"]:checked'),
      ch => $(ch).closest('tr').attr('data-role')
    );
    if (roles.length === 0) {
      Notification.error('Please select at least one role to perform this operation.');
      return null;
    }
    return roles;
  }

  async function handleClickCreateRole() {
    createRoleDialog.$dom.find('[name="role"]').val('');
    const action = await createRoleDialog.clear().open();
    if (action !== 'ok') {
      return;
    }
    const role = createRoleDialog.$dom.find('[name="role"]').val();
    await util.post('', {
      operation: 'set',
      role,
    });
    window.location.reload();
  }

  async function handleClickDeleteSelected() {
    const selectedRoles = ensureAndGetSelectedRoles();
    if (selectedRoles === null) {
      return;
    }
    const action = await new ConfirmDialog({
      $body: tpl`
        <div class="typo">
          <p>Are you sure want to delete the selected roles?</p>
          <p>Users in those roles will be removed from the domain.</p>
        </div>`,
    }).open();
    if (action !== 'yes') {
      return;
    }
    await util.post('', {
      operation: 'delete',
      role: selectedRoles,
    });
    Notification.success('Selected roles are deleted.');
    await delay(2000);
    window.location.reload();
  }

  $('[name="create_role"]').click(() => handleClickCreateRole());
  $('[name="delete_selected"]').click(() => handleClickDeleteSelected());
});

export default page;
