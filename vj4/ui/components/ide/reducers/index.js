import { combineReducers } from 'redux';
import ui from './ui';
import editor from './editor';
import pretest from './pretest';
import records from './records';
import problem from './problem';

const reducer = combineReducers({
  ui,
  editor,
  pretest,
  records,
  problem,
});

export default reducer;
