import { argv } from 'yargs';
import root from './utils/root.js';
import runGulp from './runGulp.js';
import runWebpack from './runWebpack.js';

const { watch, production } = argv;

async function main() {
  await runGulp(argv);
  runWebpack(argv);
}

process.chdir(root());
main();
