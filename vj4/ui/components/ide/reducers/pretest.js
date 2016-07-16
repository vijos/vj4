import uuid from 'uuid';

export default function reducer(state = [
  { id: uuid.v4(), input: '', output: '' },
], action) {
  switch (action.type) {
  default:
    return state;
  }
}
