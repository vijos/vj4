import { NamedPage } from '../misc/PageLoader';
import 'codemirror/lib/codemirror.css';

const page = new NamedPage('problem_detail', () => {
  require.ensure([
    'codemirror/lib/codemirror.js',
    '../components/ide/ide',
    'react',
    'react-dom',
    'react-codemirror',
  ], (require) => {
    require('react-codemirror');
    const Ide = require('../components/ide/ide').default;
    const React = require('react');
    const ReactDOM = require('react-dom');
    ReactDOM.render(
      (<Ide />),
      document.getElementById('ide')
    );
  });
  /* Initialize IDE */
  const enterIdeMode = () => {
    $('body').addClass('ide-mode');
  };
  const leaveIdeMode = () => {
    $('body').removeClass('ide-mode');
  };
  /* url hash changes */
  if (window.location.hash) {
    const hash = window.location.hash;
    if (hash === '#ide') {
      enterIdeMode();
    }
  }
  $(window).on('hashchange', () => {
    /* On entering IDE mode */
    if (window.location.hash === '#ide') {
      enterIdeMode();
    }
  });
});

export default page;
