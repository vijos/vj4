import _ from 'lodash';

import { NamedPage } from '../misc/PageLoader';

import Notification from '../components/notification';
import { ConfirmDialog, ActionDialog } from '../components/dialog';
import UserSelectAutoComplete from '../components/autocomplete/UserSelectAutoComplete';

import * as util from '../misc/Util';
import tpl from '../utils/tpl';
import delay from '../utils/delay';

const page = new NamedPage('domain_user', () => {
  const addUserSelector = UserSelectAutoComplete.getOrConstruct($('.dialog__body--add-user [name="user"]'));
  const addUserDialog = new ActionDialog({
    $body: $('.dialog__body--add-user > div'),
    onDispatch(action) {
      const $role = addUserDialog.$dom.find('[name="role"]');
      if (action === 'ok') {
        if (addUserSelector.value() === null) {
          addUserSelector.focus();
          return false;
        }
        if ($role.val() === '') {
          $role.focus();
          return false;
        }
      }
      return true;
    },
  });
  addUserDialog.clear = function () {
    addUserSelector.clear();
    this.$dom.find('[name="role"]').val('');
  };

  const setRolesDialog = new ActionDialog({
    $body: $('.dialog__body--set-role > div'),
    onDispatch(action) {
      const $role = setRolesDialog.$dom.find('[name="role"]');
      if (action === 'ok' && $role.val() === '') {
        $role.focus();
        return false;
      }
      return true;
    },
  });
  setRolesDialog.clear = function () {
    this.$dom.find('[name="role"]').val('');
    return this;
  };

  async function handleClickAddUser() {
    const action = await addUserDialog.clear().open();
    if (action !== 'ok') {
      return;
    }
    const user = addUserSelector.value();
    const role = addUserDialog.$dom.find('[name="role"]').val();
    await util.post('', {
      operation: 'set_user',
      uid: user._id,
      role,
    });
    window.location.reload();
  }

  function ensureAndGetSelectedUsers() {
    const users = _.map(
      $('.domain-users tbody [type="checkbox"]:checked'),
      ch => $(ch).closest('tr').attr('data-uid')
    );
    if (users.length === 0) {
      Notification.error('Please select at least one user to perform this operation.');
      return null;
    }
    return users;
  }

  async function handleClickRemoveSelected() {
    const selectedUsers = ensureAndGetSelectedUsers();
    if (selectedUsers === null) {
      return;
    }
    const action = await new ConfirmDialog({
      $body: tpl`
        <div class="typo">
          <p>Are you sure want to remove the selected users from this domain?</p>
          <p>Their account will not be deleted and they will have default role when visiting this domain.</p>
        </div>`,
    }).open();
    if (action !== 'yes') {
      return;
    }
    // TODO
    alert(selectedUsers.join(', '));
    Notification.success('Selected users are removed from the domain');
    await delay(2000);
    window.location.reload();
  }

  async function handleClickSetSelected() {
    const selectedUsers = ensureAndGetSelectedUsers();
    if (selectedUsers === null) {
      return;
    }
    const action = await setRolesDialog.clear().open();
    if (action !== 'ok') {
      return;
    }
    const role = setRolesDialog.$dom.find('[name="role"]').val();
    // TODO
    alert(`set role = ${role} for users = ${selectedUsers.join(', ')}`);
    Notification.success(`Role updated to ${role} for selected users`);
  }

  async function handleChangeUserRole(ev) {
    const row = $(ev.currentTarget).closest('tr');
    const role = $(ev.currentTarget).val();
    await util.post('', {
      operation: 'set_user',
      uid: row.attr('data-uid'),
      role,
    });
    Notification.success(`Role updated to ${role}`);
  }

  $('[name="add_user"]').click(() => handleClickAddUser());
  $('[name="remove_selected"]').click(() => handleClickRemoveSelected());
  $('[name="set_roles"]').click(() => handleClickSetSelected());
  $('.domain-users [name="role"]').change(ev => handleChangeUserRole(ev));
});

export default page;
