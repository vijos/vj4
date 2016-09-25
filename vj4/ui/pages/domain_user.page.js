import { NamedPage } from '../misc/PageLoader';

import { ActionDialog } from '../components/dialog';
import UserSelectAutoComplete from '../components/autocomplete/UserSelectAutoComplete';

import * as util from '../misc/Util';

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
      await util
        .post('', {
          operation: 'set_user',
          uid: user._id,
          role,
        });
      window.location.reload();
      return true;
    },
  });

  function openAddUserDialog() {
    userSelector.$dom.val('');
    addUserDialog.$dom.find('[name="role"]').val('');
    addUserDialog.open();
  }

  function handleDeleteSelected() {
    $('.domain-users tbody input[type="checkbox"]:checked').closest('tr').each((i, e) => {
      alert($(e).attr('data-uid'));
    });
  }

  function handleSetSelected() {
    $('.domain-users tbody input[type="checkbox"]:checked').closest('tr').each((i, e) => {
      alert($(e).attr('data-uid'));
    });
  }

  async function handleUserRoleChange(ev) {
    const row = $(ev.currentTarget).closest('tr');
    const role = $(ev.currentTarget).val();
    await util
      .post('', {
        operation: 'set_user',
        uid: row.attr('data-uid'),
        role,
      });
    if (role === '') {
      window.location.reload();
    }
  }

  $('[name="add_user"]').click(() => openAddUserDialog());
  $('[name="delete_selected"]').click(() => handleDeleteSelected());
  $('[name="set_roles"]').click(() => handleSetSelected());
  $('.domain-users [name="role"]').change(ev => handleUserRoleChange(ev));
});

export default page;
