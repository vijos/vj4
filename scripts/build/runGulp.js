import _ from 'lodash';
import gulp from 'gulp';
import gutil from 'gulp-util';
import chalk from 'chalk';
import gulpConfig from './config/gulp.js';

export default function ({ watch, production }, onBuiltOnce) {
  function handleError(err) {
    gutil.log(chalk.red('Error: %s'), chalk.reset(err.toString()));
    if (err && !watch) {
      process.exit(1);
      return;
    }
  }
  gulpConfig({ watch, production, errorHandler: handleError })

  gulp.on('task_start', ({ task }) => {
    gutil.log(chalk.blue(`Starting task: %s`), chalk.reset(task));
  });
  gulp.on('task_stop', ({ task }) => {
    gutil.log(chalk.green(`Finished: %s`), chalk.reset(task));
    if (task === 'default') {
      if (watch) {
        gulp.start('watch');
      }
      if (onBuiltOnce) {
        onBuiltOnce();
      }
    }
  });
  gulp.start('default');
};
