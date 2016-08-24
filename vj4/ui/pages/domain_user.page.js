import { NamedPage } from '../misc/PageLoader';

import { ActionDialog } from '../components/dialog';
import UserSelectAutoComplete from '../components/autocomplete/UserSelectAutoComplete';

const page = new NamedPage('domain_user', () => {
  const userSelector = UserSelectAutoComplete.getOrConstruct($('.dialog__body--add-user [name="user"]'));
  const addUserDialog = new ActionDialog({
    $body: $('.dialog__body--add-user > div'),
    onAction: action => {
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
      // TODO: send ajax
      alert(JSON.stringify({
        user,
        role,
      }, null, 4));
      window.location.reload();
      return true;
    },
  });

  function openAddUserDialog() {
    userSelector.$dom.val('');
    addUserDialog.$dom.find('[name="role"]').val('');
    addUserDialog.open();
  }

  function handleSelectAllChange(ev) {
    $('.domain-users tbody input[type="checkbox"]:enabled').prop('checked', $(ev.currentTarget).prop('checked'));
  }

  function handleUserRoleChange(ev) {
    const row = $(ev.currentTarget).closest('tr');
    alert(JSON.stringify({
      uid: row.attr('data-uid'),
      role: $(ev.currentTarget).val(),
    }, null, 4));
  }

  $('[name="add_user"]').click(() => openAddUserDialog());
  $('[name="delete_selected"]').click(() => alert('not implemented'));
  $('[name="set_roles"]').click(() => alert('not implemented'));
  $('.domain-users [name="role"]').change(ev => handleUserRoleChange(ev));
  $('.domain-users [name="select_all"]').change(ev => handleSelectAllChange(ev));
});

export default page;
