import uuid from 'uuid';
import _ from 'lodash';

const initialId = uuid.v4();

function isPretestValid(state) {
  for (const id of state.tabs) {
    const item = state.items[id];
    if (item.input.trim().length > 0 && item.output.trim().length > 0) {
      return true;
    }
  }
  return false;
}

export default function reducer(state = {
  counter: 1,
  current: initialId,
  tabs: [initialId],
  items: {
    [initialId]: {
      id: initialId,
      title: '#1',
      input: '',
      output: '',
    },
  },
  valid: false,
}, action) {
  switch (action.type) {
  case 'IDE_PRETEST_SWITCH_TO_DATA': {
    const currentId = action.payload;
    return {
      ...state,
      current: currentId,
    };
  }
  case 'IDE_PRETEST_ADD_DATA': {
    const newCounter = state.counter + 1;
    const newId = uuid.v4();
    return {
      ...state,
      counter: newCounter,
      current: newId,
      tabs: [...state.tabs, newId],
      items: {
        ...state.items,
        [newId]: {
          id: newId,
          title: `#${newCounter}`,
          input: '',
          output: '',
        },
      },
    };
  }
  case 'IDE_PRETEST_REMOVE_DATA': {
    const orgIdx = state.tabs.indexOf(state.current);
    let newCounter = state.counter;
    const newTabs = _.without(state.tabs, state.current);
    const newItems = _.omit(state.items, state.current);
    if (newTabs.length === 0) {
      // keep at least one data
      const id = uuid.v4();
      newTabs.push(id);
      newItems[id] = {
        id,
        title: `#${++newCounter}`,
        input: '',
        output: '',
      };
    }
    const newIdx = (orgIdx < newTabs.length) ? orgIdx : orgIdx - 1;
    const newState = {
      ...state,
      counter: newCounter,
      current: newTabs[newIdx],
      tabs: newTabs,
      items: newItems,
    };
    newState.valid = isPretestValid(newState);
    return newState;
  }
  case 'IDE_PRETEST_DATA_CHANGE': {
    const { id, type, value } = action.payload;
    const newState = {
      ...state,
      items: {
        ...state.items,
        [id]: {
          ...state.items[id],
          [type]: value,
        },
      },
    };
    newState.valid = isPretestValid(newState);
    return newState;
  }
  default:
    return state;
  }
}
