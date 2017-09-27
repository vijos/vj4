import attachObjectMeta from './util/objectMeta';

export const JOIN_METHOD_NONE = 0;
export const JOIN_METHOD_ALL = 1;
export const JOIN_METHOD_CODE = 2;
export const JOIN_METHOD_RANGE = {
  [JOIN_METHOD_NONE]: 'No user is allowed to join this domain',
  [JOIN_METHOD_ALL]: 'Any user is allowed to join this domain',
  [JOIN_METHOD_CODE]: 'Any user is allowed to join this domain with an invitation code',
};
attachObjectMeta(JOIN_METHOD_RANGE, 'intKey', true);

export const JOIN_EXPIRATION_KEEP_CURRENT = 0;
export const JOIN_EXPIRATION_UNLIMITED = -1;

export const JOIN_EXPIRATION_RANGE = {
  [JOIN_EXPIRATION_KEEP_CURRENT]: 'Keep current expiration', // this option must be placed at first
  3: '3 hours',
  24: '1 day',
  [24 * 3]: '3 days',
  [24 * 7]: '1 week',
  [24 * 30]: '1 month',
  [JOIN_EXPIRATION_UNLIMITED]: 'No expiration',
};
attachObjectMeta(JOIN_EXPIRATION_RANGE, 'intKey', true);
