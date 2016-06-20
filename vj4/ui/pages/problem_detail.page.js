import { NamedPage } from 'misc/PageLoader';
import 'codemirror/lib/codemirror.css';

const page = new NamedPage('problem_detail', () => {

  require.ensure([
    'codemirror/lib/codemirror.js',
    'components/ide/ide',
    'react',
    'react-dom',
    'react-codemirror',
  ], (require) => {
    const CodeMirror = require('react-codemirror');
    const Ide = require('components/ide/ide').default;
    const React = require('react');
    const ReactDOM = require('react-dom');

    ReactDOM.render(
      (<Ide />),
      document.getElementById('ide')
    );

  });

  /* Initialize IDE */
  const enterIdeMode = (refresh) => {
    if (refresh) {
      $('.header').addClass('header--hidden');
      $('.footer').addClass('footer--hidden');
    }
    else {
      $('.header').addClass('header--transition').addClass('header--hidden');
      $('.footer').addClass('footer--hidden');
    }
    $('.main').addClass('main--ide-mode');
  };

  const leaveIdeMode = () => {
    $('.header').removeClass('header--hidden');
  };

  /* url hash changes */
  if (window.location.hash) {
    const hash = window.location.hash;
    if (hash === '#ide') {
      enterIdeMode(true);
    }
  }

  $(window).on('hashchange', function() {
    /* On entering IDE mode */
    if (window.location.hash === '#ide') {
      enterIdeMode(false);
    }
  });

});

export default page;
