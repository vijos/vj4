import React, { PropTypes } from 'react';

class ResultItem extends React.Component {

  constructor(props) {
    super(props);

    this.state = {
      loadProgress: 0,
    };
  }

  render() {
    return (
      <li className={`result ${this.resultTypeToClassNameMap[this.props.type]}`}>
        <div className="result__progress-bg" style={{width: `${this.state.loadProgress || 0}%`}}></div>
        <span className="result__title">
          <i className="result__title__icon" />
          <span className="result__title__text">TEST</span>
        </span>
        <span className="result__state">
          <span className="result__state__items">
            <span className="result__state__items__item">
              Pending
            </span>
          </span>
        </span>
        <span className="result__statistics">
          <span className="result__statistics__running-time">{ this.props.info.runningTime }</span>
          <span className="result__statistics__memory-usage">{ this.props.info.memoryUsage }</span>
          <span className="result__statistics__start-time">{ this.props.info.startTime }</span>
        </span>
        <div className="clearfix"></div>
      </li>
    );
  }

  resultTypeToClassNameMap = {
    pending: 'result--pending',
    progress: 'result--progress',
    pass: 'result--pass',
    fail: 'result--fail',
    ignore: 'result--ignore',
  }

  static propTypes = {
    type: PropTypes.string.isRequired,
    loadProgress: PropTypes.number,
    info: PropTypes.shape({
      runningTime: PropTypes.string,
      memoryUsage: PropTypes.string,
      startTime: PropTypes.string.isRequired,
    }),
  }
}

export default ResultItem;
