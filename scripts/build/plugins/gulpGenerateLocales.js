import yaml from 'js-yaml';

import { PluginError } from 'gulp-util';
import through from 'through2';
import path from 'path';

export default function generateLocales() {

  function bufferContents(file, encoding, callback) {
    if (file.isNull()) {
      callback();
      return;
    }
    if (file.isStream()) {
      this.emit('error', new PluginError('Stream not supported'));
      callback();
      return;
    }

    const doc = yaml.safeLoad(file.contents);
    file.contents = new Buffer(`window.LOCALES = ${JSON.stringify(doc, null, 2)}`);
    file.path = path.join(
      path.dirname(file.path),
      path.basename(file.path, path.extname(file.path)) + '.js'
    );

    this.push(file);
    callback();
  }

  return through.obj(bufferContents);

};
