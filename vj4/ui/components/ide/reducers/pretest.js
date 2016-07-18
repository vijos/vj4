import uuid from 'uuid';
import _ from 'lodash';

const initialId = uuid.v4();

export default function reducer(state = {
  counter: 1,
  current: initialId,
  items: [
    { id: initialId, title: '#1', input: '', output: '' },
  ]
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
      items: [...state.items, {
        id: newId,
        title: `#${newCounter}`,
        input: '',
        output: '',
      }],
    };
  }
  case 'IDE_PRETEST_REMOVE_DATA': {
    const originalIndex = _.findIndex(state.items, item => item.id === state.current);
    let newItems = _.clone(state.items);
    _.pullAt(newItems, originalIndex);
    if (newItems.length === 0) {
      // keep at least one data
      newItems = [
        { id: uuid.v4(), title: `#${++state.counter}`, input: '', output: '' },
      ];
    }
    let newIndex = originalIndex;
    if (newIndex >= newItems.length) {
      newIndex--;
    }
    return {
      ...state,
      current: newItems[newIndex].id,
      items: newItems,
    };
  }
  default:
    return state;
  }
}
