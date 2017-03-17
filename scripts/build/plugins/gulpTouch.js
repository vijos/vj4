import { PluginError } from 'gulp-util';
import through from 'through2';
import fsp from 'fs-promise';

export default function touch(mtime) {

  async function touchFile(file) {
    const fd = await fsp.open(file.path, 'a');
    try {
      await fsp.futimes(fd, mtime, mtime);
    } finally {
      await fsp.close(fd);
    }
  }

  function processStream(file, encoding, callback) {
    if (file.isNull()) {
      callback();
      return;
    }
    if (file.isStream()) {
      this.emit('error', new PluginError('Stream not supported'));
      callback();
      return;
    }
    touchFile(file)
      .catch(err => this.emit('error', err))
      .then(() => {
        this.push(file);
        callback();
      });
  }

  return through.obj(processStream);

};
