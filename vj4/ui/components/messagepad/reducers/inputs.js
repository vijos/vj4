import _ from 'lodash';

export default function reducer(state = {}, action) {
  switch (action.type) {
  case 'DIALOGUES_LOAD_DIALOGUES_FULFILLED': {
    const dialogues = action.payload.messages;
    return _.fromPairs(_.map(dialogues, d => [d._id, '']));
  }
  case 'DIALOGUES_CREATE': {
    const { id } = action.payload;
    return {
      ...state,
      [id]: '',
    };
  }
  case 'DIALOGUES_INPUT_CHANGED': {
    const { dialogueId } = action.meta;
    return {
      ...state,
      [dialogueId]: action.payload,
    };
  }
  case 'DIALOGUES_POST_REPLY_FULFILLED': {
    const { dialogueId } = action.meta;
    return {
      ...state,
      [dialogueId]: '',
    };
  }
  case 'DIALOGUES_POST_SEND_FULFILLED': {
    const { placeholderId } = action.meta;
    return {
      ..._.omit(state, placeholderId),
      [action.payload.mdoc._id]: '',
    };
  }
  default:
    return state;
  }
}
