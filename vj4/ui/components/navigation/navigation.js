import _ from 'lodash';

class Navigation {
  constructor($nav, $navShadow) {
    this.$nav = $nav;
    this.$navShadow = $navShadow;
    this.isFloating = false;
    this.state = {};
  }

  float() {
    if (!this.isFloating) {
      this.$nav.addClass('floating');
      this.$navShadow.addClass('floating');
      this.isFloating = true;
    }
  }

  unfloat() {
    if (this.isFloating) {
      this.$nav.removeClass('floating');
      this.$navShadow.removeClass('floating');
      this.isFloating = false;
    }
  }

  update() {
    const shouldFloat = _.values(this.state).indexOf(true) > -1;
    if (shouldFloat) {
      this.float();
    } else {
      this.unfloat();
    }
  }

  setState(name, value) {
    this.state[name] = value;
    this.update();
  }
}

const nav = new Navigation($('.nav'), $('.nav--shadow'));
export default nav;
