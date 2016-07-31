import path from 'path';
import glob from 'glob-promise';
import fsp from 'fs-promise';
import yargs from 'yargs';
import _ from 'lodash';

const argv = yargs
  .usage('Usage: generate_constant.js source')
  .demand(1, 'must provide source')
  .argv;

main(argv._[0]).catch(e => console.error(e.stack));

async function main(pattern) {
  const files = await glob(pattern);
  for (let file of files) {
    const fp = path.join(process.cwd(), file);
    const dir = path.dirname(fp);
    const dest = path.join(dir, `${path.basename(fp, path.extname(fp))}.py`);
    const content = require(fp);
    await processBody(content, fp, dest);
  }
}

async function processBody(content, src, dest) {
  const fd = await fsp.open(dest, 'w');
  const emit = (...argv) => fsp.write(fd, ...argv);
  await emitBanner(emit, src);
  for (const [name, val] of _.toPairs(content)) {
    if (typeof val === 'object' && val.__exportToPython === false) {
      continue;
    }
    await emitVariable(emit, name, val);
  }
  await fsp.close(fd);
}

async function emitBanner(emit, srcFilePath) {
  const relativePath = path.relative('', srcFilePath);
  await emit(`
    """
    !!! WARNING !!!
    This file is auto-generated from \`${relativePath}\`.
    Don't edit directly, otherwise it will be overwritten.
    Run \`npm run generate:constant\` to update this file.
    """
  `.split('\n').map(l => l.trim()).join('\n'));
  await emit('\n');
}

async function emitVariable(emit, name, v) {
  await emit(`${name} = `);
  await emitLiteralOrObject(emit, v);
  await emit(`\n\n`);
}

async function emitLiteralOrObject(emit, v) {
  if (typeof v === 'number') {
    await emit(String(v));
    return;
  }
  if (typeof v === 'boolean') {
    await emit(_.capitalize(String(v)));
    return;
  }
  if (typeof v === 'string') {
    await emit(JSON.stringify(v));
    return;
  }
  if (Array.isArray(v)) {
    await emit('[');
    for (let item of v) {
      await emitLiteralOrObject(emit, item);
    }
    await emit(']');
    return;
  }
  if (v instanceof Object) {
    const { __intKey, ...val } = v;
    await emit('{\n');
    for (const [ name, item ] of _.entries(val)) {
      if (__intKey) {
        await emit(`${name}: `);
      } else {
        await emit(`${JSON.stringify(name)}: `);
      }
      await emitLiteralOrObject(emit, item);
      await emit(',\n');
    }
    await emit('}');
    return;
  }
  // null / undefined / cannot recognize
  await emit('Null');
}
