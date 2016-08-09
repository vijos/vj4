import _ from 'lodash';

export default function reducer(state = {}, action) {
  switch (action.type) {
  case 'DIALOGUES_LOAD_DIALOGUES_FULFILLED': {
    return _.keyBy(action.payload.messages, '_id');
  }
  case 'DIALOGUES_CREATE': {
    const { id, uid } = action.payload;
    return {
      ...state,
      [id]: {
        _id: id,
        sender_uid: UserContext.uid,
        sender_udoc: {
          uname: `UID = ${String(UserContext.uid)}`,
          gravatar_url: '/img/avatar.png',
        },
        sendee_uid: uid,
        sendee_udoc: {
          uname: `UID = ${String(uid)}`,
          gravatar_url: '/img/avatar.png',
        },
        reply: [],
        isPlaceholder: true,
      },
    };
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
  case 'DIALOGUES_POST_SEND_FULFILLED': {
    const { placeholderId } = action.meta;
    return {
      ..._.omit(state, placeholderId),
      [action.payload.mdoc._id]: action.payload.mdoc,
    };
  }
  default:
    return state;
  }
}
