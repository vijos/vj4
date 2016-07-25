import React from 'react';
import { connect } from 'react-redux';
import visualizeRender from '../../utils/visualizeRender';

const mapStateToProps = (state) => ({
  items: state.records.items,
});

const mergeProps = (stateProps, dispatchProps, ownProps) => ({
  ...dispatchProps,
  data: stateProps.items[ownProps.id],
});

@connect(mapStateToProps, null, mergeProps)
@visualizeRender
export default class IdeRecordsRowContainer extends React.Component {
  render() {
    return (
      <tr><td>{this.props.data._id}</td></tr>
    );
  }
}
