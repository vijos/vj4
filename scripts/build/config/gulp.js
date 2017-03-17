import _ from 'lodash';
import moment from 'moment';
import gulp from 'gulp';
import gutil from 'gulp-util';
import chalk from 'chalk';
import del from 'del';
import svgmin from 'gulp-svgmin';
import iconfont from 'gulp-iconfont';
import nunjucks from 'gulp-nunjucks';
import plumber from 'gulp-plumber';
import gulpif from 'gulp-if';
import vjGenerateConstants from '../plugins/gulpGenerateConstants';
import vjGenerateLocales from '../plugins/gulpGenerateLocales';
import vjTouch from '../plugins/gulpTouch';

let isInWatchMode = false;
const iconTimestamp = moment.utc([2017, 0, 1, 0, 0, 0, 0]).unix();

function handleWatchChange(name, r = 300) {
  return _.debounce((ev) => {
    gutil.log('File %s: %s', chalk.yellow(ev.type), ev.path);
    gulp.start(name);
  }, r);
}

function offsetMtimeAtFirstBuild() {
  // Offset the mtime at first build to
  // workaround webpack/watchpack issue #25.
  return gulpif(!isInWatchMode, vjTouch(~~((Date.now() - 30 * 1000) / 1000)));
}

export default function ({ watch, production, errorHandler }) {

  let iconfontTemplateArgs = null;

  gulp.task('iconfont:template', () => {
    return gulp.src('vj4/ui/misc/icons/template/*.styl')
      .pipe(nunjucks.compile(iconfontTemplateArgs))
      .pipe(gulp.dest('vj4/ui/misc/.iconfont'))
      .pipe(offsetMtimeAtFirstBuild())
  });

  gulp.task('iconfont', () => {
    return gulp
      .src('vj4/ui/misc/icons/*.svg')
      .pipe(plumber({ errorHandler }))
      .pipe(svgmin())
      .pipe(gulp.dest('vj4/ui/misc/icons'))
      .pipe(offsetMtimeAtFirstBuild())
      .pipe(iconfont({
        fontHeight: 1000,
        prependUnicode: false,
        descent: 6.25 / 100 * 1000,
        fontName: 'vj4icon',
        formats: ['svg', 'ttf', 'eot', 'woff', 'woff2'],
        timestamp: iconTimestamp,
      }))
      .on('glyphs', (glyphs, options) => {
        iconfontTemplateArgs = { glyphs, options };
        gulp.start('iconfont:template');
      })
      .pipe(gulp.dest('vj4/ui/misc/.iconfont'))
      .pipe(offsetMtimeAtFirstBuild());
  });

  gulp.task('constant', () => {
    return gulp
      .src('vj4/ui/constant/*.js')
      .pipe(plumber({ errorHandler }))
      .pipe(vjGenerateConstants())
      .pipe(gulp.dest('vj4/constant'))
      .pipe(offsetMtimeAtFirstBuild());
  });

  gulp.task('locale', () => {
    return gulp
      .src('vj4/locale/*.yaml')
      .pipe(plumber({ errorHandler }))
      .pipe(vjGenerateLocales())
      .pipe(gulp.dest('vj4/ui/static/locale'))
      .pipe(offsetMtimeAtFirstBuild());
  });

  gulp.task('watch', () => {
    isInWatchMode = true;
    gulp.watch('vj4/ui/misc/icons/*.svg', handleWatchChange('iconfont'));
    gulp.watch('vj4/ui/constant/*.js', handleWatchChange('constant'));
    gulp.watch('vj4/locale/*.yaml', handleWatchChange('locale'));
  });

  gulp.task('default', ['iconfont', 'constant', 'locale']);

}
