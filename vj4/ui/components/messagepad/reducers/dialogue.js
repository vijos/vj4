import _ from 'lodash';

export default function reducer(state = {
  items: {},
  activeTab: null,
}, action) {
  switch (action.type) {
  case 'DIALOGUES_LOAD_DIALOGUES_FULFILLED': {
    const dialogues = action.payload.messages;
    return {
      items: _.keyBy(dialogues, '_id'),
      activeTab: null,
    };
  }
  case 'DIALOGUES_SWITCH_TO': {
    return {
      ...state,
      activeTab: action.payload,
    };
  }
  default:
    return state;
  }
}
