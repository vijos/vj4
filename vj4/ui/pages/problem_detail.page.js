import { NamedPage } from '../misc/PageLoader';
import Navigation from '../components/navigation/navigation';

const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

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

    $('body').addClass('header--collapsed');
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

    $('body').removeClass('header--collapsed');
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
  window.extender = new ProblemPageExtender();
});

export default page;
