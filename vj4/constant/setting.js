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

export const SHOW_TAGS_ALL = 0;
export const SHOW_TAGS_PARTIALLY = 1;
export const SHOW_TAGS_HIDE = 2;
export const SHOW_TAGS_RANGE = {
  [SHOW_TAGS_ALL]: 'Show all tags',
  [SHOW_TAGS_PARTIALLY]: 'Hide categorical tags',
  [SHOW_TAGS_HIDE]: 'Hide all tags',
};
attachObjectMeta(SHOW_TAGS_RANGE, 'intKey', true);

export const FUNCTION_RANGE = {
  0: 'Disabled',
  1: 'Enabled',
};
attachObjectMeta(FUNCTION_RANGE, 'intKey', true);
