export default async function loadReactRedux(storeReducer) {
  const React = await System.import('react');
  const { render, unmountComponentAtNode } = await System.import('react-dom');
  const { Provider } = await System.import('react-redux');
  const { createStore, applyMiddleware } = await System.import('redux');
  const { default: reduxThunk } = await System.import('redux-thunk');
  const { default: reduxPromise } = await System.import('redux-promise-middleware');

  const reduxMiddlewares = [];
  reduxMiddlewares.push(reduxThunk);
  reduxMiddlewares.push(reduxPromise());

  if (process.env.NODE_ENV !== 'production') {
    const { createLogger } = await System.import('redux-logger');
    reduxMiddlewares.push(createLogger({
      collapsed: true,
      duration: true,
    }));
  }

  const store = createStore(storeReducer, applyMiddleware(...reduxMiddlewares));

  return {
    React,
    render,
    unmountComponentAtNode,
    Provider,
    store,
  };
}
