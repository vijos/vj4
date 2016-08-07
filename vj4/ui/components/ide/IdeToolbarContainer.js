import _ from 'lodash';
import React from 'react';
import { connect } from 'react-redux';
import Icon from '../react/IconComponent';
import Toolbar, {
  ToolbarItemComponent as ToolbarItem,
  ToolbarButtonComponent as ToolbarButton,
  ToolbarSplitComponent as ToolbarSplit,
} from './ToolbarComponent';

import * as util from '../../misc/Util';
import * as languageEnum from '../../../constant/language';

function isTestCaseDataValid(data) {
  return data.input.trim().length > 0 && data.output.trim().length > 0;
}

function isPretestValid(state) {
  for (const id of state.tabs) {
    return isTestCaseDataValid(state.data[id]);
  }
  return false;
}

const mapStateToProps = (state) => ({
  pretestVisible: state.ui.pretest.visible,
  recordsVisible: state.ui.records.visible,
  isPosting: state.ui.isPosting,
  editorLang: state.editor.lang,
  pretestValid: isPretestValid(state.pretest),
});

const mapDispatchToProps = (dispatch) => ({
  togglePanel(uiElement) {
    dispatch({
      type: 'IDE_UI_TOGGLE_VISIBILITY',
      payload: { uiElement },
    });
  },
  setEditorLanguage(lang) {
    dispatch({
      type: 'IDE_EDITOR_SET_LANG',
      payload: lang,
    });
  },
  postPretest(context) {
    const state = context.store.getState();
    const pretest = state.pretest;
    const testCases = pretest.tabs
      .filter(tabId => isTestCaseDataValid(pretest.data[tabId]));
    // const titles = testCases.map(tabId => pretest.meta[tabId].title);
    const inputs = testCases.map(tabId => pretest.data[tabId].input);
    const outputs = testCases.map(tabId => pretest.data[tabId].output);
    const req = util.post(Context.postPretestUrl, {
      lang: state.editor.lang,
      code: state.editor.code,
      data_input: inputs,
      data_output: outputs,
    });
    dispatch({
      type: 'IDE_POST_PRETEST',
      payload: req,
    });
  },
  postSubmit(context) {
    const state = context.store.getState();
    const req = util.post(Context.postSubmitUrl, {
      lang: state.editor.lang,
      code: state.editor.code,
    });
    dispatch({
      type: 'IDE_POST_SUBMIT',
      payload: req,
    });
  },
});

@connect(mapStateToProps, mapDispatchToProps)
export default class IdeToolbarContainer extends React.PureComponent {
  static contextTypes = {
    store: React.PropTypes.object,
  };
  render() {
    return (
      <Toolbar>
        <ToolbarButton
          disabled={this.props.isPosting || !this.props.pretestValid}
          className="ide__toolbar__pretest"
          onClick={() => this.props.postPretest(this.context)}
        >
          <Icon name="debug" />Run Pretest
        </ToolbarButton>
        <ToolbarButton
          disabled={this.props.isPosting}
          className="ide__toolbar__submit"
          onClick={() => this.props.postSubmit(this.context)}
        >
          <Icon name="play" />Submit Solution
        </ToolbarButton>
        <ToolbarItem>
          <select
            className="select"
            disabled={this.props.isPosting}
            value={this.props.editorLang}
            onChange={ev => this.props.setEditorLanguage(ev.target.value)}
          >
            {_.map(languageEnum.LANG_TEXTS, (val, key) => (
              <option value={key} key={key}>{val}</option>
            ))}
          </select>
        </ToolbarItem>
        <ToolbarSplit />
        <ToolbarButton
          activated={this.props.pretestVisible}
          onClick={() => this.props.togglePanel('pretest')}
        >
          <Icon name="edit" />Pretest
        </ToolbarButton>
        <ToolbarButton
          activated={this.props.recordsVisible}
          onClick={() => this.props.togglePanel('records')}
        >
          <Icon name="flag" />Records
        </ToolbarButton>
      </Toolbar>
    );
  }
}
