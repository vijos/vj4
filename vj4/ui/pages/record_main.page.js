import { NamedPage } from '../misc/PageLoader';

const page = new NamedPage('record_main', () => {
  require.ensure(['sockjs-client', 'diff-dom'], (require) => {
    const sockJS = require('sockjs-client');
    const DiffDOM = require('diff-dom');

    const sock = sockJS('/records-conn');
    const dd = new DiffDOM();

    sock.onmessage = (message) => {
      const msg = JSON.parse(message.data);
      // TODO(iceboy): swx template.
      const newTr = $(msg.html);
      const oldTr = $(`.record_main__table tr[data-rid="${newTr.attr('data-rid')}"]`);
      if (oldTr.length) {
        dd.apply(oldTr[0], dd.diff(oldTr[0], newTr[0]));
      } else {
        $('.record_main__table tbody').prepend(newTr);
      }
    };
  });
});

export default page;
