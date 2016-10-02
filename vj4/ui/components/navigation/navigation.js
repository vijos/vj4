import _ from 'lodash';
import responsiveCutoff from '../../responsive.inc.js';

class MultipleStateContainer {
  constructor(onStateChange, initialState = false) {
    this.onStateChange = onStateChange;
    this.states = {};
    this.currentState = initialState;
  }

  set(name, value, update = true) {
    this.states[name] = value;
    if (update) {
      this.update();
    }
  }

  get() {
    return this.states[name];
  }

  update() {
    const newState = this.getState();
    if (newState !== this.currentState) {
      this.onStateChange(newState);
      this.currentState = newState;
    }
  }

  getState() {
    return _.values(this.states).indexOf(true) > -1;
  }
}

class Navigation {
  constructor($nav, $navShadow) {
    this.updateExpandWidth = _.throttle(this.updateExpandWidthImmediate.bind(this), 200);
    this.$nav = $nav;
    this.$navRow = $nav.children('.row');
    this.$navShadow = $navShadow;
    this.floating = new MultipleStateContainer(this.updateFloating.bind(this));
    this.logoVisible = new MultipleStateContainer(this.updateLogoVisibility.bind(this));
    this.expanded = new MultipleStateContainer(this.updateExpandState.bind(this));
  }

  updateFloating(state) {
    if (state) {
      this.$nav.addClass('floating');
      this.$navShadow.addClass('floating');
    } else {
      this.$nav.removeClass('floating');
      this.$navShadow.removeClass('floating');
    }
  }

  updateLogoVisibility(state) {
    if (state) {
      this.$nav.addClass('showlogo');
    } else {
      this.$nav.removeClass('showlogo');
    }
  }

  updateExpandWidthImmediate() {
    this.$navRow.css('max-width', `${window.innerWidth}px`);
  }

  updateExpandState(state) {
    if (state) {
      $(window).on('resize', this.updateExpandWidth);
      this.updateExpandWidthImmediate();
    } else {
      $(window).off('resize', this.updateExpandWidth);
      this.$navRow.css('max-width', '');
    }
  }

  getHeight() {
    if (this.$nav.length === 0) {
      return 0;
    }
    if (window.innerWidth > responsiveCutoff.mobile) {
      return this.$nav.height();
    }
    const $slideoutNav = $('.nav--slideout-trigger');
    if ($slideoutNav.length > 0) {
      return $slideoutNav.height();
    }
    return 0;
  }
}

Navigation.instance = new Navigation($('.nav'), $('.nav--shadow'));

export default Navigation;
