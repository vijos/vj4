import _ from 'lodash';
import DOMAttachedObject from '../DOMAttachedObject';
import AutoComplete from './AutoComplete';

import tpl from '../../utils/tpl';
import * as util from '../../misc/Util';

function getText(user) {
  return user.uname;
}

function getItems(val) {
  return util.get('/user/search', { q: val });
}

function renderItem(user) {
  return tpl`
    <div class="media">
      <div class="media__left medium">
        <img class="small user-profile-avatar" src="${user.gravatar_url}" width="30" height="30">
      </div>
      <div class="media__body medium">
        <div class="user-select__uname">${user.uname}</div>
        <div class="user-select__uid">UID = ${user._id}</div>
      </div>
    </div>
  `;
}

export default class UserSelectAutoComplete extends DOMAttachedObject {

  static DOMAttachKey = 'vjUserSelectAutoCompleteInstance';

  constructor($dom) {
    super($dom);
    this.autocompleteInstance = AutoComplete.getOrConstruct(this.$dom, {
      classes: 'user-select',
      items: getItems,
      render: renderItem,
      text: getText,
    });
  }

  detach() {
    super.detach();
    this.autocompleteInstance.detach();
  }

  value() {
    return this.autocompleteInstance.value();
  }

}

_.assign(UserSelectAutoComplete, DOMAttachedObject);
