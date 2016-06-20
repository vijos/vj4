import React, { PropTypes } from 'react';
import Constants from './ide-constants';

class RecordRow extends React.Component {

  static propTypes = {
    statusCode: PropTypes.number.isRequired, /* see code to status map */
    type: PropTypes.number.isRequired,       /* test or submit */
    loadProgress: PropTypes.number,
    cases: PropTypes.array.isRequired,
    memoryKb: PropTypes.number,
    timeMs: PropTypes.number,
    objectId: PropTypes.string,
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
    }
    return `${Math.floor(diffMs / ONE_DAY)} day${Math.floor(diffMs / ONE_DAY) !== 1 ? 's' : ''} ago`;
  }

  constructor(props) {
    super(props);

    this.state = {
      loadProgress: 0,
    };
    console.log('Constants = ', Constants);
  }

  renderDetailItems() {
    const statistic = {
      AC: 0,
      WA: 0,
      TLE: 0,
      MLE: 0,
      RTE: 0,
    };
    const status = Constants.codeToStatusMap[this.props.statusCode];
    if (Constants.statusToWillShowDetail[status]) {
      this.props.cases.map(el => {
        const caseStatus = Constants.codeToStatusMap[el.status];
        statistic[Constants.statusToNotation[caseStatus]] += 1;
      });
      return [
        <span className={`result__state__items__item ${statistic.AC ?
          'result__state__items__item--pass' : 'result__state__items__item--normal'}`}
          key="AC"
        >
          AC: {statistic.AC}
        </span>,
        <span className={`result__state__items__item ${statistic.WA ?
         'result__state__items__item--fail' : 'result__state__items__item--normal'}`}
         key="WA"
        >
          WA: {statistic.WA}
        </span>,
        <span className={`result__state__items__item ${statistic.TLE ?
          'result__state__items__item--fail' : 'result__state__items__item--normal'}`}
          key="TLE"
        >
          TLE: {statistic.TLE}
        </span>,
        <span className={`result__state__items__item ${statistic.MLE ?
          'result__state__items__item--fail' : 'result__state__items__item--normal'}`}
          key="MLE"
        >
          MLE: {statistic.MLE}
        </span>,
        <span className={`result__state__items__item ${statistic.RTE ?
          'result__state__items__item--fail' : 'result__state__items__item--normal'}`}
          key="RTE"
        >
          RTE: {statistic.RTE}
        </span>,
      ];
    }
    return (
      <span className="result__state__items">
        <span className="result__state__items__item">
          {Constants.statusToContentNameMap[status]}
        </span>
      </span>
    );
  }

  render() {
    const status = Constants.codeToStatusMap[this.props.statusCode];
    const {memoryKb, timeMs} = this.props;
    const {parseMemoryUsage, parseTimeUsage, dateFromMongoObjectId, calculateDiffTime} = RecordRow;

    return (
      <li className={`result ${Constants.statusToClassNameMap[status]}`}>
        <div
          className="result__progress-bg" style={{ width: `${this.state.loadProgress || 0}%` }}>
        </div>
        <span className="result__title">
          <i className="result__title__icon" />
          <span className={`result__title__text ${(this.props.type === 1) ? 'result__title__text--pretest' : ''}`}>
            {(this.props.type === 1) ? 'TEST' : Constants.statusToNotation[status]}
          </span>
        </span>
        <span className="result__state">
          <span className="result__state__items">
            {this.renderDetailItems()}
          </span>
        </span>
        <span className="result__statistics">
          {
            Constants.statusToWillShowDetail[status] ? [
              <span className="result__statistics__running-time" key={0}>{parseMemoryUsage(memoryKb)}</span>,
              <span className="result__statistics__memory-usage" key={1}>{parseTimeUsage(timeMs)}</span>,
            ] : []
          }
          <span className="result__statistics__start-time">
            {calculateDiffTime(dateFromMongoObjectId(this.props.objectId))}
          </span>
        </span>
        <div className="clearfix"></div>
      </li>
    );
  }

}

export default RecordRow;
