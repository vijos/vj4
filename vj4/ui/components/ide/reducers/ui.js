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
  submitting: false,
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
  case 'IDE_UI_SET_VISIBILITY': {
    const { uiElement, visibility } = action.payload;
    return {
      ...state,
      [uiElement]: {
        ...state[uiElement],
        visible: visibility,
      },
    };
  }
  case 'IDE_UI_TOGGLE_VISIBILITY': {
    const { uiElement } = action.payload;
    return {
      ...state,
      [uiElement]: {
        ...state[uiElement],
        visible: !state[uiElement].visible,
      },
    };
  }
  case 'IDE_POST_PRETEST_PENDING':
  case 'IDE_POST_SUBMIT_PENDING':
  {
    return {
      ...state,
      submitting: true,
    };
  }
  case 'IDE_POST_PRETEST_FULFILLED':
  case 'IDE_POST_PRETEST_REJECTED':
  case 'IDE_POST_SUBMIT_FULFILLED':
  case 'IDE_POST_SUBMIT_REJECTED':
  {
    return {
      ...state,
      submitting: false,
    };
  }
  default:
    return state;
  }
}
