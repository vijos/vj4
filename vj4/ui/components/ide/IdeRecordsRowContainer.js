import React from 'react';
import classNames from 'classnames';
import { connect } from 'react-redux';
import moment from 'moment';
import _ from 'lodash';
import { parse as parseMongoId } from '../../utils/mongoId';

import * as recordEnum from '../../../constant/record';

const shouldShowDetail = (data) =>
  recordEnum.STATUS_IDE_SHOW_DETAIL_FLAGS[data.status];

const isPretest = (data) =>
  data.type === recordEnum.TYPE_PRETEST;

const getRecordDetail = (data) => {
  if (!shouldShowDetail(data)) {
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
    const cn = classNames('icol icol--stat', {
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
export default class IdeRecordsRowContainer extends React.Component {
  static propTypes = {
    data: React.PropTypes.shape({
      _id: React.PropTypes.string,
      status: React.PropTypes.number,
      type: React.PropTypes.number,
      time_ms: React.PropTypes.number,
      memory_kb: React.PropTypes.number,
      cases: React.PropTypes.arrayOf(React.PropTypes.shape({
        status: React.PropTypes.number,
      })),
    }),
  };
  render() {
    const { data } = this.props;
    const submitAt = moment(parseMongoId(data._id).timestamp * 1000);
    return (
      <tr>
        <td className={`col--detail record-status--border ${recordEnum.STATUS_CODES[data.status]}`}>
          <span className={`icon record-status--icon ${recordEnum.STATUS_CODES[data.status]}`}></span>
          <span className="icol icol--pretest">
            {isPretest(data)
              ? <span className={`flag record-status--background ${recordEnum.STATUS_CODES[data.status]}`}>Pretest</span>
              : ''
            }
          </span>
          {getRecordDetail(data)}
        </td>
        <td className="col--memory">
          {shouldShowDetail(data) ? `${Math.ceil(data.memory_kb / 1000)} MB` : '-'}
        </td>
        <td className="col--time">
          {shouldShowDetail(data) ? `${(data.time_ms / 1000).toFixed(1)}s` : '-'}
        </td>
        <td className="col--at">
          {submitAt.fromNow()}
        </td>
      </tr>
    );
  }
}
