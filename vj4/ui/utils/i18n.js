import * as util from '../misc/Util';

export default function i18n(s) {
  return util.get(`/i18n/${s}`);
}
