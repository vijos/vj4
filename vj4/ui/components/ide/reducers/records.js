import _ from 'lodash';

export default function reducer(state = {
  rows: [],
  items: {},
}, action) {
  switch (action.type) {
  case 'IDE_RECORDS_LOAD_SUBMISSIONS_FULFILLED': {
    const { rdocs } = action.payload;
    return {
      ...state,
      rows: _.map(rdocs, '_id').reverse(),
      items: _.keyBy(rdocs, '_id'),
    };
  }
  default:
    return state;
  }
}
