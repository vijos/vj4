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

class IdeEditorContainer extends React.Component {
  componentDidMount() {
    this.refs.editor.getCodeMirror().setOption('theme', 'vjcm');
  }
  render() {
    return (
      <CodeMirror
        value={this.props.code}
        onChange={this.props.handleUpdateCode}
        options={getOptions(this.props.lang)}
        ref="editor"
      />
    );
  }
}

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
)(IdeEditorContainer);
