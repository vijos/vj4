const defaultCode = `
#include <iostream>

using namespace std;

int main()
{
    return 0;
}
`.trim();

export default function reducer(state = {
  lang: 'cc',
  code: defaultCode,
}, action) {
  switch (action.type) {
  case 'IDE_EDITOR_UPDATE_CODE': {
    return {
      ...state,
      code: action.payload,
    };
  }
  default:
    return state;
  }
}
