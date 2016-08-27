import _ from 'lodash';
import { NamedPage } from '../misc/PageLoader';
import loadReactRedux from '../utils/loadReactRedux';

import { ActionDialog } from '../components/dialog';
import UserSelectAutoComplete from '../components/autocomplete/UserSelectAutoComplete';

const page = new NamedPage('home_messages', () => {
  async function mountComponent() {
    const SockJs = await System.import('sockjs-client');
    const { default: MessagePadApp } = await System.import('../components/messagepad');
    const { default: MessagePadReducer } = await System.import('../components/messagepad/reducers');
    const { React, render, Provider, store } = await loadReactRedux(MessagePadReducer);

    const sock = new SockJs('/home/messages-conn');
    sock.onmessage = (message) => {
      const msg = JSON.parse(message.data);
      store.dispatch({
        type: 'DIALOGUES_MESSAGE_PUSH',
        payload: msg,
      });
    };

    const userSelector = UserSelectAutoComplete.getOrConstruct($('.dialog__body--user-select [name="user"]'));
    const userSelectDialog = new ActionDialog({
      $body: $('.dialog__body--user-select > div'),
      onAction: action => {
        if (action !== 'ok') {
          return true;
        }
        const user = userSelector.value();
        if (user === null) {
          return false;
        }
        const id = _.uniqueId('PLACEHOLDER_');
        store.dispatch({
          type: 'DIALOGUES_CREATE',
          payload: {
            id,
            user,
          },
        });
        store.dispatch({
          type: 'DIALOGUES_SWITCH_TO',
          payload: id,
        });
        return true;
      },
    });

    render(
      <Provider store={store}>
        <MessagePadApp
          onAdd={() => {
            userSelector.$dom.val('');
            userSelectDialog.open();
          }}
        />
      </Provider>,
      $('#messagePad').get(0)
    );
  }
  mountComponent();
});

export default page;
