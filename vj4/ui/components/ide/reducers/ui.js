export default function reducer(state = {
  main: {
    size: '50%',
  },
  pretest: {
    visible: true,
    size: 200,
  },
  records: {
    visible: true,
    size: 200,
  },
}, action) {
  switch (action.type) {
  case 'IDE_UI_CHANGE_SIZE': {
    const { uiElement, size } = action.payload;
    return {
      ...state,
      [uiElement]: {
        ...state[uiElement],
        size,
      },
    };
  }
  default:
    return state;
  }
}
