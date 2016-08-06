export default function reducer(state = null, action) {
  switch (action.type) {
  case 'DIALOGUES_SWITCH_TO': {
    return action.payload;
  }
  default:
    return state;
  }
}
