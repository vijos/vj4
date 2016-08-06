import _ from 'lodash';

export default function reducer(state = {}, action) {
  switch (action.type) {
  case 'DIALOGUES_LOAD_DIALOGUES_FULFILLED': {
    const dialogues = action.payload.messages;
    return _.fromPairs(_.map(dialogues, d => [d._id, false]));
  }
  case 'DIALOGUES_POST_REPLY_PENDING': {
    const { dialogueId } = action.meta;
    return {
      ...state,
      [dialogueId]: true,
    };
  }
  case 'DIALOGUES_POST_REPLY_REJECTED':
  case 'DIALOGUES_POST_REPLY_FULFILLED': {
    const { dialogueId } = action.meta;
    return {
      ...state,
      [dialogueId]: false,
    };
  }
  default:
    return state;
  }
}
