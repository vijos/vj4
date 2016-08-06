import _ from 'lodash';

export default function reducer(state = {}, action) {
  switch (action.type) {
  case 'DIALOGUES_LOAD_DIALOGUES_FULFILLED': {
    return _.keyBy(action.payload.messages, '_id');
  }
  case 'DIALOGUES_POST_REPLY_FULFILLED': {
    const { dialogueId } = action.meta;
    const { reply } = action.payload;
    return {
      ...state,
      [dialogueId]: {
        ...state[dialogueId],
        reply: [
          ...state[dialogueId].reply,
          reply,
        ],
      },
    };
  }
  default:
    return state;
  }
}
