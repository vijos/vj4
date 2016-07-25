import React from 'react';
import { connect } from 'react-redux';
import DataInput from './DataInputComponent';
import visualizeRender from '../../utils/visualizeRender';

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
@visualizeRender
export default class IdePretestTabPaneContainer extends React.Component {
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
