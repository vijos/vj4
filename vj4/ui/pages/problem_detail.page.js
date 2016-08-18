import Tether from 'tether';
import { NamedPage } from '../misc/PageLoader';
import Navigation from '../components/navigation/navigation';
import loadReactRedux from '../utils/loadReactRedux';
import delay from '../utils/delay';

class ProblemPageExtender {
  constructor() {
    this.isExtended = false;
    this.inProgress = false;
    this.$content = $('.problem-content');
    this.$contentBound = this.$content.closest('.section');
    this.$scratchpadContainer = $('.scratchpad-container');
  }
  async extend() {
    if (this.inProgress) {
      return;
    }
    if (this.isExtended) {
      return;
    }
    this.inProgress = true;

    const bound = this.$contentBound
      .get(0)
      .getBoundingClientRect();

    this.$content.transition({ opacity: 0 }, { duration: 100 });
    await delay(100);

    this.$scratchpadContainer
      .css({
        left: bound.left,
        top: bound.top,
        width: bound.width,
        height: bound.height,
      })
      .show()
      .transition({
        left: 0,
        top: 0,
        width: '100%',
        height: '100%',
      }, {
        duration: 500,
        easing: 'easeOutCubic',
      });

    Navigation.instance.floating.set('scratchpad', true);
    Navigation.instance.logoVisible.set('scratchpad', true);
    Navigation.instance.expanded.set('scratchpad', true);

    $('body').addClass('header--collapsed mode--scratchpad');
    await delay(500);

    $('.main > .row').hide();
    $('.footer').hide();
    $(window).scrollTop(0);

    this.inProgress = false;
    this.isExtended = true;
  }

  async collapse() {
    if (this.inProgress) {
      return;
    }
    if (!this.isExtended) {
      return;
    }
    this.inProgress = true;

    $(window).scrollTop(0);
    $('.main > .row').show();
    $('.footer').show();

    const bound = this.$contentBound
      .get(0)
      .getBoundingClientRect();

    this.$scratchpadContainer
      .transition({
        left: bound.left,
        top: bound.top,
        width: bound.width,
        height: bound.height,
      }, {
        duration: 500,
        easing: 'easeOutCubic',
      });

    Navigation.instance.floating.set('scratchpad', false);
    Navigation.instance.logoVisible.set('scratchpad', false);
    Navigation.instance.expanded.set('scratchpad', false);

    $('body').removeClass('header--collapsed mode--scratchpad');
    await delay(500);

    this.$scratchpadContainer.hide();
    this.$content.transition({ opacity: 1 }, { duration: 100 });

    this.inProgress = false;
    this.isExtended = false;
  }

  toggle() {
    if (this.isExtended) {
      this.collapse();
    } else {
      this.extend();
    }
  }

}

const page = new NamedPage('problem_detail', async () => {
  let componentMounted = false;
  let $floatingSidebar = null;
  const extender = new ProblemPageExtender();

  async function scratchpadFadeIn() {
    $('#scratchpad').transition({
      opacity: 1,
    }, {
      duration: 200,
      easing: 'easeOutCubic',
    });
    await delay(200);
  }

  async function scratchpadFadeOut() {
    $('#scratchpad').transition({
      opacity: 0,
    }, {
      duration: 200,
      easing: 'easeOutCubic',
    });
    await delay(200);
  }

  function updateFloatingSidebar() {
    $floatingSidebar.tether.position();
  }

  async function createSidebar() {
    $floatingSidebar = $('.section--problem-sidebar')
      .clone()
      .addClass('scratchpad__sidebar visible')
      .appendTo('body');
    $floatingSidebar.find('a').attr('target', '_blank');
    $floatingSidebar.tether = new Tether({
      element: $floatingSidebar,
      offset: '-20px 20px',
      target: '.scratchpad__problem',
      attachment: 'top right',
      targetAttachment: 'top right',
    });
    await delay(100);
    $floatingSidebar.tether.position();
  }

  async function removeSidebar() {
    $floatingSidebar.tether.destroy();
    $floatingSidebar.remove();
    $floatingSidebar = null;
  }

  async function mountComponent() {
    if (componentMounted) {
      return;
    }

    $('.loader-container').show();

    const SockJs = await System.import('sockjs-client');
    const { default: ScratchpadApp } = await System.import('../components/scratchpad');
    const { default: ScratchpadReducer } = await System.import('../components/scratchpad/reducers');
    const { React, render, Provider, store } = await loadReactRedux(ScratchpadReducer);

    const sock = new SockJs('/records-conn');
    sock.onmessage = (message) => {
      const msg = JSON.parse(message.data);
      store.dispatch({
        type: 'SCRATCHPAD_RECORDS_PUSH',
        payload: msg,
      });
    };

    store.dispatch({
      type: 'SCRATCHPAD_PROBLEM_SET_HTML',
      payload: $('.problem-content').html(),
    });

    render(
      <Provider store={store}>
        <ScratchpadApp />
      </Provider>,
      $('#scratchpad').get(0)
    );
    componentMounted = true;

    $('.loader-container').hide();
  }

  async function enterScratchpadMode() {
    await extender.extend();
    await mountComponent();
    await scratchpadFadeIn();
    await createSidebar();
  }

  async function leaveScratchpadMode() {
    await removeSidebar();
    await scratchpadFadeOut();
    await extender.collapse();
  }

  $(document).on('vjScratchpadRelayout', updateFloatingSidebar);
  $(document).on('click', '.action--problem-sidebar__open-scratchpad', ev => {
    enterScratchpadMode();
    ev.preventDefault();
  });
  $(document).on('click', '.action--problem-sidebar__quit-scratchpad', ev => {
    leaveScratchpadMode();
    ev.preventDefault();
  });
});

export default page;
