import { NamedPage } from '../misc/PageLoader';
import UserSelectAutoComplete from '../components/autocomplete/UserSelectAutoComplete';

const page = new NamedPage('record_main', async () => {
  const SockJs = await System.import('sockjs-client');
  const DiffDOM = await System.import('diff-dom');

  const sock = new SockJs('/records-conn');
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
  UserSelectAutoComplete.getOrConstruct($('.filter-user [name="uid_or_name"]'), {
    clearDefaultValue: false,
  });
});

export default page;
