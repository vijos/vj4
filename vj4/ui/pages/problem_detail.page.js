import { NamedPage } from '../misc/PageLoader';
import 'codemirror/lib/codemirror.css';

let ideRendered = false;

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
    const enterIdeMode = () => {
      $('body').addClass('ide-mode');
      if (!ideRendered) {
        /* Clone problem detail DOMs */
        const cloneNode = document.getElementById('node-problem-content').cloneNode(true);
        document.getElementById('node-ide-problem-content').appendChild(cloneNode);
        /* Initialize IDE */
        ReactDOM.render(
          (<Ide />),
          document.getElementById('ide')
        );
        ideRendered = true;
      }
    };
    const leaveIdeMode = () => {
      $('body').removeClass('ide-mode');
    };
    /* check url hash on refreshing */
    if (window.location.hash) {
      const hash = window.location.hash;
      if (hash === '#ide') {
        enterIdeMode();
      } else {
        leaveIdeMode();
      }
    }
    $(window).on('hashchange', () => {
      /* On entering IDE mode */
      if (window.location.hash === '#ide') {
        enterIdeMode();
      }
    });
  });
});

export default page;
