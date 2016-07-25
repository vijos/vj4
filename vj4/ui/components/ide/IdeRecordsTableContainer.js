import React from 'react';
import { connect } from 'react-redux';
import visualizeRender from '../../utils/visualizeRender';
import IdeRecordsRow from './IdeRecordsRowContainer';

const mapStateToProps = (state) => ({
  rows: state.records.rows,
});

@connect(mapStateToProps)
@visualizeRender
export default class IdeRecordsTableContainer extends React.Component {
  render() {
    return (
      <table className="data-table">
        <colgroup>
          <col />
          <col />
          <col />
          <col />
        </colgroup>
        <tbody>
          {this.props.rows.map(rowId => (
            <IdeRecordsRow key={rowId} id={rowId} />
          ))}
        </tbody>
      </table>
    );
  }
}
