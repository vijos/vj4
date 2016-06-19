import React, { PropTypes } from 'react';
import './ide.styl';
import Codemirror from 'react-codemirror';


class Ide extends React.Component {

  constructor(props) {
    super(props);
  }

  render() {
    return (
      <div className="ide-layout--table">

        <div className="ide-layout--table-row">
          <div className="ide-layout--table ide__code-area">
            <div className="ide-layout--table-row ide__code-area__toolbar">
              <div className="float-layout--left">
                <button className="ide__code-area__toolbar__btn">
                  <i className="icon-debug" style={{color: 'rgb(252, 93, 95)'}} />
                  <span>测试</span>
                </button
                ><button className="ide__code-area__toolbar__btn">
                <i className="icon-play" style={{color: 'rgb(21, 151, 71)'}} />
                <span>递交代码</span>
              </button>
              </div>
              <div className="float-layout--right">
                <label className="ide__code-area__toolbar__label">
                  <i className="icon-edit" style={{color: 'rgb(90, 88, 88)'}} />
                  <span>测试数据</span>
                </label>
                <label className="ide__code-area__toolbar__label">
                  <i className="icon-flag" style={{color: 'rgb(90, 88, 88)'}} />
                  <span>评测结果</span>
                </label>
                <button className="ide__code-area__toolbar__btn">
                  <i className="icon-settings" style={{color: 'rgb(90, 88, 88)'}} />
                  <span>编辑器设置</span>
                </button>
              </div>
            </div>
            <div className="ide-layout--table-row">
              <div className="ide-layout--table">
                <Codemirror id="code-area" options={
                  {lineNumbers: true}
                } />
              </div>
            </div>
          </div>
        </div>

        <div className="ide-layout--table-row">
          <div className="ide-layout--table ide__testing-area">
            <div className="ide-layout--table-row ide__testing-area__toolbar">
              <div className="float-layout--left">
                <div className="ide__testing-area__toolbar__title">
                  <i className="icon-edit" />
                  <span>测试数据</span>
                </div>
                <div className="toolbar-tabs">
                  <div className="tab">
                    <span>#1</span>
                  </div>
                  <div className="tab tab--active">
                    <span>#2</span>
                  </div>
                  <div className="tab">
                    <span>#3</span>
                  </div>
                  <div className="tab">
                    <span>#4</span>
                  </div>
                </div>
              </div>
              <div className="float-layout--right">
                <div className="ide__testing-area__toolbar__operations">
                  <div className="operation">保存</div>
                  <div className="operation">取消</div>
                  <div className="operation">创建</div>
                  <div className="operation"><i className="icon-close" /></div>
                </div>
              </div>
            </div>
            <div className="ide-layout--table-row">
              <div className="ide-layout--table">
                <div className="ide-layout--table-row">
                  <div className="ide-layout--table-cell" style={{'minWidth': '50%'}}>
                    <div className="ide-layout--table ide__testing-area__text-input">
                      <Codemirror id="test-input-area" className="" options= {{}} />
                      <div className="test-input-footer">样例输入</div>
                    </div>
                  </div>
                  <div className="ide-layout--table-cell" style={{'minWidth': '50%'}}>
                    <div className="ide-layout--table ide__testing-area__text-output">
                      <Codemirror id="test-output-area" className="" options= {{}} />
                      <div className="test-input-footer">样例输出</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="ide-layout--table-row">
          <div className="ide__evaluating-area">
            <div className="ide-layout--table">
              <div className="ide-layout--table-row ide__evaluating-area__toolbar">
                <div className="float-layout--left">
                  <div className="ide__evaluating-area__toolbar__title">
                    <i className="icon-flag" />
                    <span>评测结果</span>
                  </div>
                  <div className="toolbar-tabs">
                    <div className="tab tab--active">
                      <span>ALL</span>
                    </div>
                  </div>
                </div>
                <div className="float-layout--right">
                  <div className="ide__evaluating-area__toolbar__operations">
                    <div className="operation"><i className="icon-close" /></div>
                  </div>
                </div>
              </div>
              <div className="ide-layout--table-row">
                <div className="ide__evaluating-area__results">
                  <ul className="results">
                    <li className="result result--pending">
                      <div className="result__progress-bg" style={{'width': '30%'}}></div>
                      <span className="result__title">
                        <i className="result__title__icon icon-schedule" />
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
                        <span className="result__statistics__running-time">0.8s</span>
                        <span className="result__statistics__memory-usage">121MB</span>
                        <span className="result__statistics__start-time">just now</span>
                      </span>
                      <div className="clearfix"></div>
                    </li>
                    <li className="result result--judging"></li>
                    <li className="result result--ac"></li>
                    <li className="result result--err"></li>
                    <li className="result result--err"></li>
                    <li className="result result--err"></li>
                    <li className="result result--err"></li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>

      </div>
    );
  }

  static propTypes = {

  }
}

export default Ide;
