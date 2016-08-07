import _ from 'lodash';

export default function reducer(state = {}, action) {
  switch (action.type) {
  case 'DIALOGUES_LOAD_DIALOGUES_FULFILLED': {
    const dialogues = action.payload.messages;
    return _.fromPairs(_.map(dialogues, d => [d._id, false]));
  }
  case 'DIALOGUES_CREATE': {
    const { id } = action.payload;
    return {
      ...state,
      [id]: false,
    };
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
  case 'DIALOGUES_POST_SEND_PENDING': {
    const { placeholderId } = action.meta;
    return {
      ...state,
      [placeholderId]: true,
    };
  }
  case 'DIALOGUES_POST_SEND_REJECTED': {
    const { placeholderId } = action.meta;
    return {
      ...state,
      [placeholderId]: false,
    };
  }
  case 'DIALOGUES_POST_SEND_FULFILLED': {
    const { placeholderId } = action.meta;
    return {
      ..._.omit(state, placeholderId),
      [action.payload.mdoc._id]: false,
    };
  }
  default:
    return state;
  }
}
