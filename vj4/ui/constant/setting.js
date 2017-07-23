import attachObjectMeta from './util/objectMeta';

export const PRIVACY_PUBLIC = 0;
export const PRIVACY_REGISTERED_ONLY = 1;
export const PRIVACY_SECRET = 2;
export const PRIVACY_RANGE = {
  [PRIVACY_PUBLIC]: 'Public',
  [PRIVACY_REGISTERED_ONLY]: 'Visible to registered users',
  [PRIVACY_SECRET]: 'Secret',
};
attachObjectMeta(PRIVACY_RANGE, 'intKey', true);

export const FUNCTION_RANGE = {
  0: 'Disabled',
  1: 'Enabled',
};
attachObjectMeta(FUNCTION_RANGE, 'intKey', true);

export const BACKGROUND_RANGE = {
  1: '1',
  2: '2',
  3: '3',
  4: '4',
  5: '5',
  6: '6',
  7: '7',
  8: '8',
  9: '9',
  10: '10',
  11: '11',
  12: '12',
  13: '13',
  14: '14',
  15: '15',
  16: '16',
  17: '17',
  18: '18',
  19: '19',
  20: '20',
  21: '21',
};
attachObjectMeta(BACKGROUND_RANGE, 'intKey', true);
