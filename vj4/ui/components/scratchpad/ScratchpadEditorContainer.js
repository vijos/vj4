import React from 'react';
import { connect } from 'react-redux';
import CodeMirror from 'react-codemirror';

import 'codemirror/addon/edit/matchbrackets';
import 'codemirror/mode/clike/clike';
import 'codemirror/mode/pascal/pascal';
import 'codemirror/mode/python/python';

import * as languageEnum from '../../constant/language';

const getOptions = (lang) => ({
  lineNumbers: true,
  tabSize: 4,
  indentUnit: 4,
  indentWithTabs: true,
  mode: languageEnum.LANG_CODEMIRROR_MODES[lang],
});

const mapStateToProps = (state) => ({
  code: state.editor.code,
  lang: state.editor.lang,
});

const mapDispatchToProps = (dispatch) => ({
  handleUpdateCode: (code) => {
    dispatch({
      type: 'SCRATCHPAD_EDITOR_UPDATE_CODE',
      payload: code,
    });
  },
});

@connect(mapStateToProps, mapDispatchToProps)
export default class ScratchpadEditorContainer extends React.PureComponent {
  componentDidMount() {
    this.refs.editor.getCodeMirror().setOption('theme', 'vjcm');
  }
  render() {
    return (
      <CodeMirror
        value={this.props.code}
        onChange={code => this.props.handleUpdateCode(code)}
        options={getOptions(this.props.lang)}
        ref="editor"
      />
    );
  }
}
