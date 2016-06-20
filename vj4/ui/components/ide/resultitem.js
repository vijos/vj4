import React, { PropTypes } from 'react';

class ResultItem extends React.Component {

  static propTypes = {
    statusCode: PropTypes.number.isRequired, /* see code to status map */
    type: PropTypes.number.isRequired,       /* test or submit */
    loadProgress: PropTypes.number,
    cases: PropTypes.array.isRequired,
    memoryKb: PropTypes.number,
    timeMs: PropTypes.number,
    objectId: PropTypes.string,
  }

  static codeToStatusMap = {
    0: 'STATUS_WAITING',
    1: 'STATUS_ACCEPTED',
    2: 'STATUS_WRONG_ANSWER',
    3: 'STATUS_TIME_LIMIT_EXCEEDED',
    4: 'STATUS_MEMORY_LIMIT_EXCEEDED',
    5: 'STATUS_OUTPUT_LIMIT_EXCEEDED',
    6: 'STATUS_RUNTIME_ERROR',
    7: 'STATUS_COMPILE_ERROR',
    8: 'STATUS_SYSTEM_ERROR',
    9: 'STATUS_CANCELED',
    10: 'STATUS_ETC',
    20: 'STATUS_JUDGING',
    21: 'STATUS_COMPILING',
    30: 'STATUS_IGNORED',
  }

  static statusToClassNameMap = {
    STATUS_WAITING: 'result--pending',
    STATUS_ACCEPTED: 'result--pass',
    STATUS_WRONG_ANSWER: 'result--fail',
    STATUS_TIME_LIMIT_EXCEEDED: 'result--fail',
    STATUS_MEMORY_LIMIT_EXCEEDED: 'result--fail',
    STATUS_OUTPUT_LIMIT_EXCEEDED: 'result--fail',
    STATUS_RUNTIME_ERROR: 'result--fail',
    STATUS_COMPILE_ERROR: 'result--fail',
    STATUS_SYSTEM_ERROR: 'result--fail',
    STATUS_CANCELED: 'result--ignore',
    STATUS_ETC: 'result--fail',
    STATUS_JUDGING: 'result--progress',
    STATUS_COMPILING: 'result--progress',
    STATUS_IGNORED: 'result--ignore',
  }

  static statusToNotation = {
    STATUS_WAITING: 'PENDING',
    STATUS_ACCEPTED: 'AC',
    STATUS_WRONG_ANSWER: 'WA',
    STATUS_TIME_LIMIT_EXCEEDED: 'TLE',
    STATUS_MEMORY_LIMIT_EXCEEDED: 'MLE',
    STATUS_OUTPUT_LIMIT_EXCEEDED: 'OLE',
    STATUS_RUNTIME_ERROR: 'RE',
    STATUS_COMPILE_ERROR: 'CE',
    STATUS_SYSTEM_ERROR: 'IE',
    STATUS_CANCELED: 'CANCELED',
    STATUS_ETC: 'IE',
    STATUS_JUDGING: 'WAITING',
    STATUS_COMPILING: 'WAITING',
    STATUS_IGNORED: 'IGNORED',
  }

  static statusToContentNameMap = {
    STATUS_WAITING: 'Pending',
    STATUS_ACCEPTED: 'Accepted',
    STATUS_WRONG_ANSWER: 'Wrong Answer',
    STATUS_TIME_LIMIT_EXCEEDED: 'Time Limit Exceeded',
    STATUS_MEMORY_LIMIT_EXCEEDED: 'Memory Limit Exceeded',
    STATUS_OUTPUT_LIMIT_EXCEEDED: 'Output Limit Exceeded',
    STATUS_RUNTIME_ERROR: 'Runtime Error',
    STATUS_COMPILE_ERROR: 'Compile Error',
    STATUS_SYSTEM_ERROR: 'System Error',
    STATUS_CANCELED: 'Canceled',
    STATUS_ETC: 'Unknown Error',
    STATUS_JUDGING: 'Judging',
    STATUS_COMPILING: 'Compiling',
    STATUS_IGNORED: 'Ignored',
  }

  static statusToWillShowDetail = {
    STATUS_WAITING: false,
    STATUS_ACCEPTED: true,
    STATUS_WRONG_ANSWER: true,
    STATUS_TIME_LIMIT_EXCEEDED: true,
    STATUS_MEMORY_LIMIT_EXCEEDED: true,
    STATUS_RUNTIME_ERROR: true,
    STATUS_COMPILE_ERROR: false,
    STATUS_SYSTEM_ERROR: false,
    STATUS_CANCELED: false,
    STATUS_ETC: false,
    STATUS_JUDGING: false,
    STATUS_COMPILING: false,
    STATUS_IGNORED: false,
  }

  static parseMemoryUsage(memKb) {
    return (memKb < 1000) ? `${memKb} KB` : `${memKb / 1000} MB`;
  }

  static parseTimeUsage(timeMs) {
    return (timeMs < 100) ? `${timeMs} ms` : `${timeMs / 1000} s`;
  }

  static dateFromMongoObjectId(objectId) {
    return new Date(parseInt(objectId.substring(0, 8), 16) * 1000);
  }

  static calculateDiffTime(creationTime) {
    const currentTime = new Date();
    const diffMs = currentTime.getTime() - creationTime.getTime();

    const ONE_DAY = 1000 * 60 * 60 * 24;
    const ONE_HOUR = 1000 * 60 * 60;
    const ONE_MINUTE = 1000 * 60;

    if (diffMs < ONE_MINUTE) {
      return 'just now';
    } else if (diffMs < ONE_HOUR) {
      return `${Math.floor(diffMs / ONE_MINUTE)} minute${Math.floor(diffMs / ONE_MINUTE) !== 1 ? 's' : ''} ago`;
    } else if (diffMs < ONE_DAY) {
      return `${Math.floor(diffMs / ONE_HOUR)} hour${Math.floor(diffMs / ONE_DAY) !== 1 ? 's' : ''} ago`;
    } else {
      return `${Math.floor(diffMs / ONE_DAY)} day${Math.floor(diffMs / ONE_DAY) !== 1 ? 's' : ''} ago`;
    }
  }

  constructor(props) {
    super(props);

    this.state = {
      loadProgress: 0,
    };
  }

  renderDetailItems() {
    const statistic = {
      AC: 0,
      WA: 0,
      TLE: 0,
      MLE: 0,
      RTE: 0,
    };
    const status = ResultItem.codeToStatusMap[this.props.statusCode];
    if (ResultItem.statusToWillShowDetail[status]) {
      this.props.cases.map(el => {
        const caseStatus = ResultItem.codeToStatusMap[el.status];
        return statistic[ResultItem.statusToNotation[caseStatus]] += 1;
      });
      return (
        <span className="result__state__items">
          <span className={`result__state__items__item ${statistic.AC ?
          'result__state__items__item--pass' : 'result__state__items__item--normal'}`}>
            AC: {statistic.AC}
          </span>
          <span className={`result__state__items__item ${statistic.WA ?
           'result__state__items__item--fail' : 'result__state__items__item--normal'}`}>
            WA: {statistic.WA}
          </span>
          <span className={`result__state__items__item ${statistic.TLE ?
          'result__state__items__item--fail' : 'result__state__items__item--normal'}`}>
            TLE: {statistic.TLE}
          </span>
          <span className={`result__state__items__item ${statistic.MLE ?
          'result__state__items__item--fail' : 'result__state__items__item--normal'}`}>
            MLE: {statistic.MLE}
          </span>
          <span className={`result__state__items__item ${statistic.RTE ?
          'result__state__items__item--fail' : 'result__state__items__item--normal'}`}>
            RTE: {statistic.RTE}
          </span>
        </span>
      );
    }
    else {
      return (
        <span className="result__state__items">
          <span className="result__state__items__item">
            {ResultItem.statusToContentNameMap[status]}
          </span>
        </span>
      );
    }
  }

  render() {
    const status = ResultItem.codeToStatusMap[this.props.statusCode];
    const {memoryKb, timeMs} = this.props;
    const {parseMemoryUsage, parseTimeUsage, dateFromMongoObjectId, calculateDiffTime} = ResultItem;

    return (
      <li className={`result ${ResultItem.statusToClassNameMap[status]}`}>
        <div
          className="result__progress-bg" style={{ width: `${this.state.loadProgress || 0}%` }}>
        </div>
        <span className="result__title">
          <i className="result__title__icon" />
          <span className={`result__title__text ${(this.props.type === 1) ? 'result__title__text--pretest' : ''}`}>
            {(this.props.type === 1) ? 'TEST' : ResultItem.statusToNotation[status]}
          </span>
        </span>
        <span className="result__state">
          {this.renderDetailItems()}
        </span>
        <span className="result__statistics">
          {(() =>
            ResultItem.statusToWillShowDetail[status] ? [
              <span className="result__statistics__running-time" key={0}>{parseMemoryUsage(memoryKb)}</span>,
              <span className="result__statistics__memory-usage" key={1}>{parseTimeUsage(timeMs)}</span>
            ] : []).call(this)}
          <span className="result__statistics__start-time">
            {calculateDiffTime(dateFromMongoObjectId(this.props.objectId))}
          </span>
        </span>
        <div className="clearfix"></div>
      </li>
    );
  }

}

export default ResultItem;
