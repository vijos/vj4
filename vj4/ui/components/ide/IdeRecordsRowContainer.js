import React from 'react';
import classNames from 'classnames';
import { connect } from 'react-redux';
import moment from 'moment';
import _ from 'lodash';
import visualizeRender from '../../utils/visualizeRender';
import { parse as parseMongoId } from '../../utils/mongoId';

import * as recordEnum from '../../../constant/record';

const getRecordDetail = (data, showDetail) => {
  if (!showDetail) {
    return (
      <span className={`record-status--text ${recordEnum.STATUS_CODES[data.status]}`}>
        {recordEnum.STATUS_TEXTS[data.status]}
      </span>
    );
  }
  const stat = _.pick(
    _.groupBy(data.cases || [], 'status'),
    _.keys(recordEnum.STATUS_IDE_SHORT_TEXTS)
  );
  return _.map(recordEnum.STATUS_IDE_SHORT_TEXTS, (text, status) => {
    const count = (stat[status] && stat[status].length) || 0;
    const cn = classNames({
      'record-status--text': count > 0,
      [recordEnum.STATUS_CODES[data.status]]: count > 0,
    });
    return (
      <span key={text} className={cn}>
        {text}: {count}
      </span>
    );
  });
};

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
    const { status, memory_kb, time_ms } = this.props.data;
    const submitAt = moment(parseMongoId(this.props.data._id).timestamp * 1000);
    const showDetail = recordEnum.STATUS_IDE_SHOW_DETAIL_FLAGS[status];
    return (
      <tr>
        <td className={`record-status--border ${recordEnum.STATUS_CODES[status]}`}>
          <span className={`icon record-status--icon ${recordEnum.STATUS_CODES[status]}`}></span>
          {getRecordDetail(this.props.data, showDetail)}
        </td>
        <td>
          {showDetail ? `${Math.ceil(memory_kb / 1000)} MB` : ''}
        </td>
        <td>
          {showDetail ? `${(time_ms / 1000).toFixed(1)}s` : ''}
        </td>
        <td>
          {submitAt.fromNow()}
        </td>
      </tr>
    );
  }
}
