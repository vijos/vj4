import React from 'react';
import './ide.styl';
import Codemirror from 'react-codemirror';
import RecordRow from './record-row';
import _ from 'lodash';
import sockJS from 'sockjs-client';
import { post } from '../../misc/Util';
import Constants from './ide-constants';

import 'codemirror/mode/clike/clike';
import 'codemirror/mode/pascal/pascal';
import 'codemirror/mode/python/python';
import 'codemirror/mode/javascript/javascript';
import 'codemirror/mode/ruby/ruby';
import 'codemirror/mode/php/php';

class Ide extends React.Component {

  static spanSupportLanguageList() {
    return Object.keys(Constants.supportLangTypes).map((key, idx) =>
      <option value={key} key={idx}>{Constants.supportLangTypes[key]}</option>
    );
  }

  constructor(props) {
    super(props);
    this.state = {
      displayTesting: true,
      displayEvalutating: true,
      code: '',
      currentTestingInputText: '',
      currentTestingOutputText: '',
      language: 'c',
      testingData: [],
      resultData: [],
      currentActiveTabIndex: -1,
      codeAreaOptions: {
        lineNumbers: true,
        matchBrackets: true,
        readOnly: false,
        indentUnit: 4,
        // mode: Ide.mapLangToMode[this.state.language],
        extraKeys: {
          Tab: (cm) => {
            const spaces = Array(cm.getOption('indentUnit') + 1).join(' ');
            cm.replaceSelection(spaces, 'end', '+input');
          },
        },
      },
    };
    this.sock = null;
  }

  componentDidMount() {
    if (!this.sock) {
      this.sock = sockJS('/records-conn');
      this.sock.onmessage = (message) => {
        const rdoc = JSON.parse(message.data).rdoc;
        // console.log('Received rdoc = ', rdoc);
        /* Check uid and pid to ensure that the record should be shown */
        if ((window.UserContext.uid.toString() !== rdoc.udoc._id.toString())
          || (window.Context.problemId.toString() !== rdoc.pid.toString())) {
          return;
        }
        const nextResultData = this.state.resultData.slice();
        const existedRdoc = nextResultData.filter(val => val._id === rdoc._id)[0];
        if (existedRdoc) {
          const idx = nextResultData.indexOf(existedRdoc);
          nextResultData[idx] = rdoc;
        } else {
          nextResultData.unshift(rdoc);
        }
        return this.setState({
          resultData: nextResultData,
        });
      };
    }
  }

  componentWillUnmount() {
    if (this.sock) {
      this.sock.close();
      this.sock = null;
    }
  }

  onLeaveIDEMode() {
    if (window.confirm('确认退出IDE模式吗？')) {
      window.location.hash = '';
    }
  }

  onLanguageChange(ev) {
    this.setState({
      language: ev.target.value,
    });
    this.refs.editor.getCodeMirror().setOption('mode', Constants.mapLangToMode[ev.target.value]);
  }

  onCodeUpdate(newCode) {
    this.setState({
      code: newCode,
    });
  }

  onAddTestCase(ev, cb = () => {}) {
    const newTestcase = {
      input: '',
      output: '',
    };
    const nextTestingData = _.cloneDeep(this.state.testingData);
    nextTestingData.push(newTestcase);
    this.setState({
      currentTestingInputText: '',
      currentTestingOutputText: '',
      testingData: nextTestingData,
      currentActiveTabIndex: nextTestingData.length - 1,
    }, cb);
  }

  onDeleteTestCase() {
    const nextTestingData = _.cloneDeep(this.state.testingData);
    nextTestingData.splice(this.state.currentActiveTabIndex, 1);
    let nextActiveTabIndex = 0;

    if ((this.state.currentActiveTabIndex === 0) && (this.state.testingData.length !== 1)) {
      nextActiveTabIndex = 0;
    } else if ((this.state.currentActiveTabIndex === 0) && (this.state.testingData.length === 1)) {
      return this.setState({
        currentTestingInputText: '',
        currentTestingOutputText: '',
        testingData: [],
        currentActiveTabIndex: -1,
      });
    } else {
      nextActiveTabIndex = this.state.currentActiveTabIndex - 1;
    }
    return this.setState({
      testingData: nextTestingData,
      currentActiveTabIndex: nextActiveTabIndex,
      currentTestingInputText: nextTestingData[nextActiveTabIndex].input,
      currentTestingOutputText: nextTestingData[nextActiveTabIndex].output,
    });
  }

  spanClickTestCaseTabCallback(idx) {
    return () => {
      this.setState({
        currentActiveTabIndex: idx,
        currentTestingInputText: this.state.testingData[idx].input,
        currentTestingOutputText: this.state.testingData[idx].output,
      });
    };
  }

  onUpdateTestingCaseInput(ev) {
    const newText = ev.target.value;
    const callback = () => {
      const nextTestingData = _.cloneDeep(this.state.testingData);
      nextTestingData[this.state.currentActiveTabIndex].input = newText;
      this.setState({
        currentTestingInputText: newText,
        testingData: nextTestingData,
      });
    };
    if (this.state.testingData.length === 0) {
      this.onAddTestCase(null, callback.bind(this));
    } else {
      callback();
    }
  }

  onUpdateTestingCaseOutput(ev) {
    const newText = ev.target.value;
    const callback = () => {
      const nextTestingData = _.cloneDeep(this.state.testingData);
      nextTestingData[this.state.currentActiveTabIndex].output = newText;
      this.setState({
        currentTestingOutputText: newText,
        testingData: nextTestingData,
      });
    };
    if (this.state.testingData.length === 0) {
      this.onAddTestCase(null, callback);
    } else {
      callback();
    }
  }

  onTestingSubmit() {
    if (!this.state.testingData.length) {
      return;
    }
    const dataInput = this.state.testingData.map(el => el.input);
    const dataOutput = this.state.testingData.map(el => el.output);
    const pid = window.Context.problemId;
    post(`/p/${pid}/pretest`, {
      lang: this.state.language,
      code: this.state.code,
      data_input: dataInput,
      data_output: dataOutput,
    });
  }

  onProblemSubmit() {
    const pid = window.Context.problemId;
    post(`/p/${pid}/submit`, {
      lang: this.state.language,
      code: this.state.code,
    });
  }

  toggleDisplayEvaluating() {
    this.setState({
      displayEvalutating: !this.state.displayEvalutating,
    });
  }

  toggleDisplayTesting() {
    this.setState({
      displayTesting: !this.state.displayTesting,
    });
  }

  renderTestingTabList() {
    return this.state.testingData.map((el, idx) =>
      <div
        className={`tab ${(this.state.currentActiveTabIndex === idx) ? 'tab--active' : ''}`}
        key={idx}
        onClick={this.spanClickTestCaseTabCallback(idx).bind(this)}
      >
        <span>#{idx + 1}</span>
      </div>
    );
  }

  renderEvaluatingResultList() {
    return this.state.resultData.map(
      (rdoc, idx) => <RecordRow
        objectId={rdoc._id}
        statusCode={rdoc.status}
        type={rdoc.type}
        memoryKb={rdoc.memory_kb || 0}
        timeMs={rdoc.time_ms || 0}
        cases={rdoc.cases || []}
        key={rdoc._id}
      />
    );
  }

  render() {
    const codeAreaOptions = {
      ...this.state.codeAreaOptions,
      mode: Constants.mapLangToMode[this.state.language],
    };
    // console.log(`this.state = `, this.state);
    // window.vm = this;
    return (
      <div className="ide-layout--table">

        <div className="ide-layout--table-row">
          <div className="ide-layout--table ide__code-area">
            <div className="ide-layout--table-row ide__code-area__toolbar">
              <div className="float-layout--left">
                <button
                  className="ide__code-area__toolbar__btn ide__code-area__toolbar__btn--pretest"
                  disabled={this.state.testingData.length ? undefined : 'disabled'}
                  onClick={this.onTestingSubmit.bind(this)}
                >
                  <i className="icon-debug" />
                  <span>测试</span>
                </button>
                <button
                  className="ide__code-area__toolbar__btn ide__code-area__toolbar__btn--submit"
                  onClick={this.onProblemSubmit.bind(this)}
                >
                  <i className="icon-play" />
                  <span>递交代码</span>
                </button>
                <button
                  className="ide__code-area__toolbar__btn ide__code-area__toolbar__btn--exit"
                  onClick={this.onLeaveIDEMode}
                >
                  <i className="icon-close" />
                  <span>退出IDE模式</span>
                </button>
              </div>
              <div className="float-layout--right">
                <label
                  className={'ide__code-area__toolbar__label ' + (this.state.displayTesting ? 'ide__code-area__toolbar__label--active' : '')}
                  onClick={this.toggleDisplayTesting.bind(this)}
                >
                  <i className="icon-edit" />
                  <span>测试数据</span>
                </label>
                <label
                  className={'ide__code-area__toolbar__label ' + (this.state.displayEvalutating ? 'ide__code-area__toolbar__label--active' : '')}
                  onClick={this.toggleDisplayEvaluating.bind(this)}
                >
                  <i className="icon-flag" />
                  <span>评测结果</span>
                </label>
                {/*
                <button className="ide__code-area__toolbar__btn">
                  <i className="icon-settings" />
                  <span>编辑器设置</span>
                </button>
                */}
                <select onChange={this.onLanguageChange.bind(this)} >
                  {Ide.spanSupportLanguageList()}
                </select>
              </div>
            </div>
            <div className="ide-layout--table-row">
              <div className="ide-layout--table">
                <Codemirror id="code-area" ref="editor"
                            options={codeAreaOptions}
                            onChange={this.onCodeUpdate.bind(this)} />
              </div>
            </div>
          </div>
        </div>

        <div className="ide-layout--table-row" style={{display: this.state.displayTesting ? undefined : 'none'}}>
          <div className="ide-layout--table ide__testing-area">
            <div className="ide-layout--table-row ide__testing-area__toolbar">
              <div className="float-layout--left">
                <div className="ide__testing-area__toolbar__title">
                  <i className="icon-edit" />
                  <span>测试数据</span>
                </div>
                <div className="toolbar-tabs">
                  { this.renderTestingTabList() }
                </div>
              </div>
              <div className="float-layout--right">
                <div className="ide__testing-area__toolbar__operations">
                  <div className="operation" onClick={this.onAddTestCase.bind(this)}>创建</div>
                  <div className="operation" onClick={this.onDeleteTestCase.bind(this)}>删除</div>
                  <div className="operation" onClick={this.toggleDisplayTesting.bind(this)}>
                    <i className="icon-close" />
                  </div>
                </div>
              </div>
            </div>
            <div className="ide-layout--table-row">
              <div className="ide-layout--table">
                <div className="ide-layout--table-row">
                  <div className="ide-layout--table-cell" style={{'minWidth': '50%'}}>
                    <div className="ide-layout--table ide__testing-area__text-input">
                      <div className="ide-layout--table-row">
                        <textarea
                          ref="testingInput"
                          wrap="off"
                          value={this.state.currentTestingInputText}
                          onChange={this.onUpdateTestingCaseInput.bind(this)}
                        />
                      </div>
                      <div className="ide-layout--table-row test-input-footer">样例输入</div>
                    </div>
                  </div>
                  <div className="ide-layout--table-cell" style={{'minWidth': '50%'}}>
                    <div className="ide-layout--table ide__testing-area__text-output">
                      <div className="ide-layout--table-row">
                        <textarea ref="testingOutput" wrap="off"
                                value={this.state.currentTestingOutputText}
                                onChange={this.onUpdateTestingCaseOutput.bind(this)} />
                      </div>
                      <div className="ide-layout--table-row test-input-footer">样例输出</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="ide-layout--table-row" style={{display: this.state.displayEvalutating ? undefined : 'none'}}>
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
                    <div className="operation" onClick={this.toggleDisplayEvaluating.bind(this)}>
                      <i className="icon-close" />
                    </div>
                  </div>
                </div>
              </div>
              <div className="ide-layout--table-row">
                <div className="ide__evaluating-area__results">
                  <ul className="results">
                    { this.renderEvaluatingResultList() }
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>

      </div>
    );
  }

}
export default Ide;
