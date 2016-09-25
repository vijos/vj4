import _ from 'lodash';

import { NamedPage } from '../misc/PageLoader';

import Notification from '../components/notification';
import { ConfirmDialog, ActionDialog } from '../components/dialog';
import UserSelectAutoComplete from '../components/autocomplete/UserSelectAutoComplete';

import * as util from '../misc/Util';
import tpl from '../utils/tpl';

const page = new NamedPage('domain_user', () => {
  const userSelector = UserSelectAutoComplete.getOrConstruct($('.dialog__body--add-user [name="user"]'));
  const addUserDialog = new ActionDialog({
    $body: $('.dialog__body--add-user > div'),
    onAction: async action => {
      if (action !== 'ok') {
        return true;
      }
      const user = userSelector.value();
      if (user === null) {
        return false;
      }
      const role = addUserDialog.$dom.find('[name="role"]').val();
      if (role === '') {
        return false;
      }
      await util.post('', {
        operation: 'set_user',
        uid: user._id,
        role,
      });
      window.location.reload();
      return true;
    },
  });
  const setRolesDialog = new ActionDialog({
    $body: $('.dialog__body--set-role > div'),
    onAction: action => {
      if (action !== 'ok') {
        return true;
      }
      const role = addUserDialog.$dom.find('[name="role"]').val();
      if (role === '') {
        return false;
      }
      alert(role);
    },
  });

  function openAddUserDialog() {
    userSelector.$dom.val('');
    addUserDialog.$dom.find('[name="role"]').val('');
    addUserDialog.open();
  }

  function getSelectedUsers() {
    return _.map(
      $('.domain-users tbody [type="checkbox"]:checked'),
      ch => $(ch).closest('tr').attr('data-uid')
    );
  }

  function ensureAndGetSelectedUsers() {
    const users = getSelectedUsers();
    if (users.length === 0) {
      Notification.error('Please select at least one user to perform this operation.');
      return null;
    };
    return users;
  }

  function handleDeleteSelected() {
    const selectedUsers = ensureAndGetSelectedUsers();
    if (selectedUsers === null) {
      return;
    }
    new ConfirmDialog({
      $body: tpl`
        <div class="typo">
          <p>Are you sure want to remove the selected users from this domain?</p>
          <p>Their account will not be deleted and they will have default role when visiting this domain.</p>
        </div>`,
      onAction: action => {
        if (action !== 'yes') {
          return true;
        }
        alert(selectedUsers.join(', '));
        return true;
      },
    }).open();
  }

  function handleSetSelected() {
    const selectedUsers = ensureAndGetSelectedUsers();
    if (selectedUsers === null) {
      return;
    }
    setRolesDialog.$dom.find('[name="role"]').val('');
    setRolesDialog.open();
    /*
    $('.domain-users tbody input[type="checkbox"]:checked').closest('tr').each((i, e) => {
      alert($(e).attr('data-uid'));
    });*/
  }

  async function handleUserRoleChange(ev) {
    const row = $(ev.currentTarget).closest('tr');
    const role = $(ev.currentTarget).val();
    await util.post('', {
      operation: 'set_user',
      uid: row.attr('data-uid'),
      role,
    });
  }

  $('[name="add_user"]').click(() => openAddUserDialog());
  $('[name="delete_selected"]').click(() => handleDeleteSelected());
  $('[name="set_roles"]').click(() => handleSetSelected());
  $('.domain-users [name="role"]').change(ev => handleUserRoleChange(ev));
});

export default page;
