import _ from 'lodash';
import gulp from 'gulp';
import log from 'fancy-log';
import chalk from 'chalk';
import gulpConfig from './config/gulp.js';

export default async function ({ watch, production, constant }) {
  function handleError(err) {
    log(chalk.red('Error: %s'), chalk.reset(err.toString()));
    if (err && !watch) {
      process.exit(1);
      return;
    }
  }
  const gulpTasks = gulpConfig({ watch, production, errorHandler: handleError });
  return new Promise(resolve => {
    let taskList = {};

    gulp.on('start', ({ uid, name }) => {
      log(chalk.blue(`Starting task: %s`), chalk.reset(name));
      taskList[uid] = true;
    });
    gulp.on('stop', ({ uid, name }) => {
      log(chalk.green(`Finished: %s`), chalk.reset(name));
      taskList[uid] = false;

      if (Object.values(taskList).filter(b => b).length === 0) {
        if (watch) {
          gulpTasks['watch']();
        }
        resolve();
      }
    });

    if (constant) {
      gulpTasks['constant']();
    } else {
      gulpTasks['default']();
    }
  });
};
