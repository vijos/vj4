import React, { PropTypes } from 'react';
import CodeMirror from 'codemirror';

class CodeArea extends React.Component {

  constructor(props) {
    super(props);
    this.state = {
      codeMirrorObj: null,
    };
  }

  componentDidMount() {
    const cmObj = CodeMirror.fromTextArea(
      document.getElementById(this.props.id),
      this.props.options
    );
    /*this.setState({
      codeMirrorObj: cmObj,
    });*/
  }

  render() {
    return (<textarea id={this.props.id} />);
  }

  static propTypes = {
    id: PropTypes.string.isRequired,
    options: PropTypes.object.isRequired,
  }
}

export default CodeArea;
