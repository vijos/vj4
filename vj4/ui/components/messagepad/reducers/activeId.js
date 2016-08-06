export default function reducer(state = null, action) {
  switch (action.type) {
  case 'DIALOGUES_SWITCH_TO': {
    return action.payload;
  }
  case 'DIALOGUES_CREATE': {
    return action.payload.id;
  }
  case 'DIALOGUES_POST_SEND_FULFILLED': {
    return action.payload.mdoc._id;
  }
  default:
    return state;
  }
}
