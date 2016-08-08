import { NamedPage } from '../misc/PageLoader';
import loadReactRedux from '../utils/loadReactRedux';

const page = new NamedPage('home_messages', async () => {
  const SockJs = await System.import('sockjs-client');

  const sock = new SockJs('/home/messages-conn');
  sock.onmessage = (message) => {
    alert(message.data);
  };

  async function mountComponent() {
    const { default: MessagePadApp } = await System.import('../components/messagepad');
    const { default: MessagePadReducer } = await System.import('../components/messagepad/reducers');
    const { React, render, Provider, store } = await loadReactRedux(MessagePadReducer);
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
