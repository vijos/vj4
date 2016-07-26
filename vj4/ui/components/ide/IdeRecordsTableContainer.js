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
      <table className="data-table ide-records__table">
        <colgroup>
          <col className="col--detail" />
          <col className="col--memory" />
          <col className="col--time" />
          <col className="col--at" />
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
