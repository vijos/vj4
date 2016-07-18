import { combineReducers } from 'redux';
import ui from './ui';
import editor from './editor';
import pretest from './pretest';

const reducer = combineReducers({
  ui,
  editor,
  pretest,
});

export default reducer;
