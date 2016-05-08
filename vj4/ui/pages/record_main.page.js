import { NamedPage } from 'misc/PageLoader';

const page = new NamedPage('record_main', () => {

  require.ensure(['sockjs-client', 'diff-dom'], (require) => {

    const SockJS = require('sockjs-client');
    const diffDOM = require('diff-dom');

    const sock = SockJS('/records-conn');
    const dd = new diffDOM();

    sock.onmessage = (message) => {
      const msg = JSON.parse(message.data);
      // TODO(iceboy): swx template.
      const new_tr = $(msg.html);
      const old_tr = $(`.record_main__table tr[data-rid="${new_tr.attr('data-rid')}"]`);
      if (old_tr.length) {
        dd.apply(old_tr[0], dd.diff(old_tr[0], new_tr[0]));
      } else {
        $('.record_main__table tbody').prepend(new_tr);
      }
    };

  });

});

export default page;
