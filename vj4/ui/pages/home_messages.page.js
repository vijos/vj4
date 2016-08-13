import { NamedPage } from '../misc/PageLoader';
import loadReactRedux from '../utils/loadReactRedux';

const page = new NamedPage('home_messages', async () => {
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

    render(
      <Provider store={store}>
        <MessagePadApp />
      </Provider>,
      $('#messagePad').get(0)
    );
  }
  mountComponent();
});

export default page;
