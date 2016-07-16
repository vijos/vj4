import { combineReducers } from 'redux';
import editor from './editor';
import ui from './ui';

const reducer = combineReducers({
  editor,
  ui,
});

export default reducer;
