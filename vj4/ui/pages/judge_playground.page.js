import { NamedPage } from '../misc/PageLoader';

const page = new NamedPage('judge_playground', async () => {
  const SockJs = await System.import('sockjs-client');

  const sock = new SockJs('/judge/consume-conn');

  sock.onopen = () => {
    $('<div>').append('Connection opened').appendTo('#messages');
  };

  sock.onmessage = (message) => {
    const msg = JSON.parse(message.data);
    const div = $('<div>').text(message.data).appendTo('#messages');

    const send = (key, packet) => {
      const data = {
        ...packet,
        key,
        tag: msg.tag,
      };
      sock.send(JSON.stringify(data));
    };

    $('<button>').text('Compile')
      .on('click', () => {
        send('next', { status: 20 });
      })
      .appendTo(div);

    $('<button>').text('Point0')
      .on('click', () => {
        send('next', {
          case: { status: 2, score: 0, time_ms: 1, memory_kb: 777 },
          judge_text: 'oops',
        });
      })
      .appendTo(div);

    $('<button>').text('Point10')
      .on('click', () => {
        send('next', {
          case: { status: 1, score: 10, time_ms: 1, memory_kb: 233 },
          judge_text: 'well done',
        });
      })
      .appendTo(div);

    $('<button>').text('Accept')
      .on('click', () => {
        send('end', { status: 1, score: 100, time_ms: 1, memory_kb: 1 });
        $('button', div).detach();
      })
      .appendTo(div);

    $('<button>').text('WA')
      .on('click', () => {
        send('end', { status: 2, score: 88, time_ms: 88, memory_kb: 88 });
        $('button', div).detach();
      })
      .appendTo(div);
  };

  sock.onclose = (message) => {
    $('<div>')
      .append(`Connection closed, reason=${JSON.stringify(message.reason)}`)
      .appendTo('#messages');
  };
});

export default page;
