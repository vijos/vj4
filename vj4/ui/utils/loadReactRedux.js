export default async function loadReactRedux(storeReducer) {
  const React = await System.import('react');
  const { render } = await System.import('react-dom');
  const { Provider } = await System.import('react-redux');
  const { createStore, applyMiddleware } = await System.import('redux');
  const { default: reduxThunk } = await System.import('redux-thunk');
  const { default: reduxPromise } = await System.import('redux-promise-middleware');

  const reduxMiddlewares = [];
  reduxMiddlewares.push(reduxThunk);
  reduxMiddlewares.push(reduxPromise());

  if (process.env.NODE_ENV !== 'production') {
    const reduxLogger = await System.import('redux-logger');
    reduxMiddlewares.push(reduxLogger({
      collapsed: true,
      duration: true,
    }));
  }

  const store = createStore(storeReducer, applyMiddleware(...reduxMiddlewares));

  return {
    React,
    render,
    Provider,
    store,
  };
}
