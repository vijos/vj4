import _ from 'lodash';

export default function tpl(pieces, ...substitutions) {
  let result = pieces[0];
  for (let i = 0; i < substitutions.length; ++i) {
    result += _.escape(substitutions[i]) + pieces[i + 1];
  }
  return result;
}
