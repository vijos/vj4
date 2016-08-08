import attachObjectMeta from './util/objectMeta';

export const USER_GENDER_MALE = 0;
export const USER_GENDER_FEMALE = 1;
export const USER_GENDER_OTHER = 2;
export const USER_GENDERS = [USER_GENDER_MALE, USER_GENDER_FEMALE, USER_GENDER_OTHER];
export const USER_GENDER_RANGE = {
  [USER_GENDER_MALE]: 'Cis Male / Cis Man ♂',
  [USER_GENDER_FEMALE]: 'Cis Female / Cis Woman ♀',
  [USER_GENDER_OTHER]: 'Other',
};
attachObjectMeta(USER_GENDER_RANGE, 'intKey', true);
