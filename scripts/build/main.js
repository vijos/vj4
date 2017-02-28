import { argv } from 'yargs';
import root from './utils/root.js';
import runGulp from './runGulp.js';
import runWebpack from './runWebpack.js';

const { watch, production } = argv;

process.chdir(root());

runGulp(argv, () => {
  runWebpack(argv);
});
