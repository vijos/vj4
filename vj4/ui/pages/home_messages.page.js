import { NamedPage } from '../misc/PageLoader';
import delay from '../utils/delay';

const page = new NamedPage('home_messages', async () => {
  async function mountComponent() {
    const React = await System.import('react');
    const { render } = await System.import('react-dom');
    const { Provider } = await System.import('react-redux');
    const { createStore, applyMiddleware } = await System.import('redux');
    const { default: reduxThunk } = await System.import('redux-thunk');
    const reduxPromise = await System.import('redux-promise-middleware');
    const reduxLogger = await System.import('redux-logger');
    const { default: MessagePadApp } = await System.import('../components/messagepad');
    const { default: MessagePadReducer } = await System.import('../components/messagepad/reducers');

    const reduxMiddlewares = [];
    reduxMiddlewares.push(reduxThunk);
    reduxMiddlewares.push(reduxPromise());
    reduxMiddlewares.push(reduxLogger({
      collapsed: true,
      duration: true,
    }));

    const store = createStore(MessagePadReducer, applyMiddleware(...reduxMiddlewares));

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
