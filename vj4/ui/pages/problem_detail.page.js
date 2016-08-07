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
    this.$ideContainer = $('.ide-container');
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

    this.$ideContainer
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

    Navigation.instance.floating.set('ide', true);
    Navigation.instance.logoVisible.set('ide', true);
    Navigation.instance.expanded.set('ide', true);

    $('body').addClass('header--collapsed mode--ide');
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

    this.$ideContainer
      .transition({
        left: bound.left,
        top: bound.top,
        width: bound.width,
        height: bound.height,
      }, {
        duration: 500,
        easing: 'easeOutCubic',
      });

    Navigation.instance.floating.set('ide', false);
    Navigation.instance.logoVisible.set('ide', false);
    Navigation.instance.expanded.set('ide', false);

    $('body').removeClass('header--collapsed mode--ide');
    await delay(500);

    this.$ideContainer.hide();
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

  async function ideFadeIn() {
    $('#ide').transition({
      opacity: 1,
    }, {
      duration: 200,
      easing: 'easeOutCubic',
    });
    await delay(200);
  }

  async function ideFadeOut() {
    $('#ide').transition({
      opacity: 0,
    }, {
      duration: 200,
      easing: 'easeOutCubic',
    });
    await delay(200);
  }

  async function createSidebar() {
    $floatingSidebar = $('.section--problem-sidebar')
      .clone()
      .addClass('ide__sidebar')
      .appendTo('body');
    $floatingSidebar.find('a').attr('target', '_blank');
    $floatingSidebar.tether = new Tether({
      element: $floatingSidebar,
      offset: '-20px 20px',
      target: '.ide__problem',
      attachment: 'top right',
      targetAttachment: 'top right',
    });
    $floatingSidebar.tether.position();
    $floatingSidebar.addClass('visible');
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
    const { default: IdeApp } = await System.import('../components/ide');
    const { default: IdeReducer } = await System.import('../components/ide/reducers');
    const { React, render, Provider, store } = await loadReactRedux(IdeReducer);

    const sock = new SockJs('/records-conn');
    sock.onmessage = (message) => {
      const msg = JSON.parse(message.data);
      store.dispatch({
        type: 'IDE_RECORDS_PUSH',
        payload: msg,
      });
    };

    store.dispatch({
      type: 'IDE_PROBLEM_SET_HTML',
      payload: $('.problem-content').html(),
    });

    render(
      <Provider store={store}>
        <IdeApp />
      </Provider>,
      $('#ide').get(0)
    );
    componentMounted = true;

    $('.loader-container').hide();
  }

  async function enterIdeMode() {
    await extender.extend();
    await mountComponent();
    await ideFadeIn();
    await createSidebar();
  }

  async function leaveIdeMode() {
    await removeSidebar();
    await ideFadeOut();
    await extender.collapse();
  }

  $(document).on('click', '.action--problem-sidebar__ide', enterIdeMode);
  $(document).on('click', '.action--problem-sidebar__leave-ide', leaveIdeMode);
});

export default page;
