import _ from 'lodash';

let newContent;

function print(str) {
  newContent += str;
}

function processBody(content) {
  printBanner();
  for (const [name, val] of _.toPairs(content)) {
    if (typeof val === 'object' && val.__exportToPython === false) {
      continue;
    }
    printVariable(name, val);
  }
}

function printBanner() {
  print(`
    """
    !!! WARNING !!!
    This file is auto-generated. Don't edit directly,
    otherwise it will be overwritten.
    Run \`npm run generate:constant\` to update this file.
    """

    import collections
  `.split('\n').map(l => l.trim()).join('\n'));
  print('\n');
}

function printVariable(name, v) {
  print(`${name} = `);
  printLiteralOrObject(v);
  print(`\n\n`);
}

function printLiteralOrObject(v) {
  if (typeof v === 'number') {
    print(String(v));
    return;
  }
  if (typeof v === 'boolean') {
    print(_.capitalize(String(v)));
    return;
  }
  if (typeof v === 'string') {
    print(JSON.stringify(v));
    return;
  }
  if (Array.isArray(v)) {
    print('[');
    for (let item of v) {
      printLiteralOrObject(item);
      print(',');
    }
    print(']');
    return;
  }
  if (v instanceof Object) {
    const { __intKey, ...val } = v;
    print('collections.OrderedDict([\n');
    for (const [ name, item ] of _.entries(val)) {
      print('(');
      if (__intKey) {
        print(name);
      } else {
        print(JSON.stringify(name));
      }
      print(', ');
      printLiteralOrObject(item);
      print('),\n');
    }
    print('])');
    return;
  }
  print('None');
}

export default function transformConstant(filePath) {
  newContent = '';
  // Invalidate require cache
  delete require.cache[require.resolve(filePath)]
  const content = require(filePath);
  processBody(content);
  return newContent;
}

transformConstant.getPackageContent = function(modules) {
  return modules.map(m => `from vj4.constant import ${m}`).join('\n') + '\n';
}
