import attachObjectMeta from './util/objectMeta';

export const RULE_OI = 2;
export const RULE_ACM = 3;

export const RULE_ID = {
  [RULE_OI]: 'oi',
  [RULE_ACM]: 'acm',
};
attachObjectMeta(RULE_ID, 'intKey', true);

export const RULE_TEXTS = {
  [RULE_OI]: 'OI',
  [RULE_ACM]: 'ACM/ICPC',
};
attachObjectMeta(RULE_TEXTS, 'intKey', true);
