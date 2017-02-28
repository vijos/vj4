import _ from 'lodash';

export default function mapWebpackUrlPrefix(mapList) {
  const rules = mapList.map(mappingRule => {
    const regex = mappingRule.prefix.split('/').map(s => _.escapeRegExp(s)).join('[\\/\\\\]');
    return {
      from: new RegExp(`^${regex}`, mappingRule.flag),
      to: mappingRule.replace,
    };
  });
  return function mapUrl(url) {
    rules.forEach(rule => {
      url = url.replace(rule.from, rule.to);
    });
    return url;
  };
}
