import attachObjectMeta from './util/objectMeta';

export const PRIVACY_RANGE = {
  0: 'Public',
  1: 'Visible to users',
  2: 'Not public',
};
attachObjectMeta(PRIVACY_RANGE, 'intKey', true);

export const SHOW_TAGS_RANGE = {
  0: 'Show all tags',
  1: 'Hide categorical tags',
  2: 'Hide all tags',
};
attachObjectMeta(SHOW_TAGS_RANGE, 'intKey', true);

export const SEND_CODE_RANGE = {
  0: 'No',
  1: 'Yes',
};
attachObjectMeta(SEND_CODE_RANGE, 'intKey', true);
