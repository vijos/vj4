import React from 'react';
import { connect } from 'react-redux';
import CodeMirror from 'react-codemirror';
import visualizeRender from '../../utils/visualizeRender';

import 'codemirror/addon/edit/matchbrackets';
import 'codemirror/mode/clike/clike';
import 'codemirror/mode/pascal/pascal';
import 'codemirror/mode/python/python';

import * as languageEnum from '../../../constant/language';

const getOptions = (lang) => ({
  lineNumbers: true,
  tabSize: 4,
  mode: languageEnum.LANG_CODEMIRROR_MODES[lang],
});

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

@connect(mapStateToProps, mapDispatchToProps)
@visualizeRender
export default class IdeEditorContainer extends React.Component {
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
