import gulp from 'gulp';
import del from 'del';
import svgmin from 'gulp-svgmin';
import iconfont from 'gulp-iconfont';
import nunjucks from 'gulp-nunjucks';
import vjGenerateConstant from './scripts/build/constant/gulp';
import vjGenerateLocale from './scripts/build/locale/gulp';

const iconTimestamp = ~~(Date.now() / 1000);

gulp.task('iconfont', () => {
  return gulp
    .src('vj4/ui/misc/icons/*.svg')
    .pipe(svgmin())
    .pipe(gulp.dest('vj4/ui/misc/icons'))
    .pipe(iconfont({
      fontHeight: 1000,
      prependUnicode: false,
      descent: 6.25 / 100 * 1000,
      fontName: 'vj4icon',
      formats: ['svg', 'ttf', 'eot', 'woff', 'woff2'],
      timestamp: iconTimestamp,
    }))
    .on('glyphs', (glyphs, options) => {
      gulp
        .src(`vj4/ui/misc/icons/template/*.styl`)
        .pipe(nunjucks.compile({ glyphs, options }))
        .pipe(gulp.dest('vj4/ui/misc/.iconfont'));
    })
    .pipe(gulp.dest('vj4/ui/misc/.iconfont'));
});

gulp.task('constant', () => {
  return gulp
    .src('vj4/ui/constant/*.js')
    .pipe(vjGenerateConstant())
    .pipe(gulp.dest('vj4/constant'));
});

gulp.task('locale', () => {
  return gulp
    .src('vj4/locale/*.yaml')
    .pipe(vjGenerateLocale())
    .pipe(gulp.dest('vj4/ui/static/locale'));
});

gulp.task('default', ['iconfont', 'constant', 'locale'], () => {});
