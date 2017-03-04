import transformConstant from '../utils/transformConstant';

import { PluginError } from 'gulp-util';
import through from 'through2';
import path from 'path';

export default function generateConstants() {

  let lastFile = null;
  const packages = [];

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
    lastFile = file;

    const moduleName = path.basename(file.path, path.extname(file.path));
    file.contents = new Buffer(transformConstant(file.path));
    file.path = path.join(path.dirname(file.path), `${moduleName}.py`);
    packages.push(moduleName);

    this.push(file);
    callback();
  }

  function endStream(callback) {
    if (!lastFile || packages.length === 0) {
      callback();
      return;
    }
    const packageFile = lastFile.clone({contents: false});
    packageFile.path = path.join(path.dirname(lastFile.path), '__init__.py');
    packageFile.contents = new Buffer(transformConstant.getPackageContent(packages));

    this.push(packageFile);
    callback();
  }

  return through.obj(bufferContents, endStream);

};
