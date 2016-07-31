import React from 'react';
import { connect } from 'react-redux';
import DataInput from './DataInputComponent';

const mapStateToProps = (state) => ({
  data: state.pretest.data,
});

const mapDispatchToProps = (dispatch) => ({
  handleDataChange(id, type, value) {
    dispatch({
      type: 'IDE_PRETEST_DATA_CHANGE',
      payload: {
        id,
        type,
        value,
      },
    });
  },
});

const mergeProps = (stateProps, dispatchProps, ownProps) => ({
  ...dispatchProps,
  id: ownProps.id,
  input: stateProps.data[ownProps.id] ? stateProps.data[ownProps.id].input : '',
  output: stateProps.data[ownProps.id] ? stateProps.data[ownProps.id].output : '',
});

@connect(mapStateToProps, mapDispatchToProps, mergeProps)
export default class IdePretestTabPaneContainer extends React.Component {
  static propTypes = {
    id: React.PropTypes.string,
    input: React.PropTypes.string,
    output: React.PropTypes.string,
    handleDataChange: React.PropTypes.func,
  };
  render() {
    return (
      <div className="flex-row flex-fill">
        <DataInput
          title="Sample Input"
          value={this.props.input}
          onChange={v => this.props.handleDataChange(this.props.id, 'input', v)}
        />
        <DataInput
          title="Sample Output"
          value={this.props.output}
          onChange={v => this.props.handleDataChange(this.props.id, 'output', v)}
        />
      </div>
    );
  }
}
