import { NamedPage } from '../misc/PageLoader';
import loadReactRedux from '../utils/loadReactRedux';

const page = new NamedPage('home_messages', async () => {
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
