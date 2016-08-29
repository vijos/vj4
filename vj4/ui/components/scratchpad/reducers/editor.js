const defaultCode = `
#include <iostream>

using namespace std;

int main()
{
\treturn 0;
}
`.trim();

export default function reducer(state = {
  lang: 'cc',
  code: defaultCode,
}, action) {
  switch (action.type) {
  case 'SCRATCHPAD_EDITOR_UPDATE_CODE': {
    return {
      ...state,
      code: action.payload,
    };
  }
  case 'SCRATCHPAD_EDITOR_SET_LANG': {
    return {
      ...state,
      lang: action.payload,
    };
  }
  default:
    return state;
  }
}
