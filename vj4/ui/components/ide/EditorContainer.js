import React from 'react';
import { connect } from 'react-redux';
import CodeMirror from 'react-codemirror';

import 'codemirror/addon/edit/matchbrackets';
import 'codemirror/mode/clike/clike';
import 'codemirror/mode/pascal/pascal';
import 'codemirror/mode/python/python';
import 'codemirror/mode/javascript/javascript';
import 'codemirror/mode/ruby/ruby';
import 'codemirror/mode/php/php';

const getOptions = (lang) => ({
  lineNumbers: true,
  tabSize: 4,
  mode: 'text/x-c++src',
});

const EditorContainer = (props) => (
  <CodeMirror
    value={props.code}
    onChange={props.handleUpdateCode}
    options={getOptions(props.lang)}
  />
);

const mapStateToProps = (state) => ({
  code: state.editor.code,
  lang: state.editor.lang,
});

const mapDispatchToProps = (dispatch) => ({
  handleUpdateCode: (code) => {
    dispatch({
      type: 'IDE_EDITOR_UPDATE_CODE',
      payload: code,
    });
  },
});

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(EditorContainer);
