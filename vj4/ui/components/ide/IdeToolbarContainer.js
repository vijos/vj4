import _ from 'lodash';
import React from 'react';
import { connect } from 'react-redux';
import Icon from './IconComponent';
import Toolbar, {
  ToolbarItemComponent as ToolbarItem,
  ToolbarButtonComponent as ToolbarButton,
  ToolbarSplitComponent as ToolbarSplit,
} from './ToolbarComponent';

import * as util from '../../misc/Util';
import * as languageEnum from '../../../constant/language';

const IdeToolbarContainer = (props, context) => (
  <Toolbar>
    <ToolbarButton
      disabled={props.submitting || !props.pretestValid}
      className="ide-toolbar__pretest"
      onClick={() => props.postPretest(context)}
    >
      <Icon name="debug" />Run Pretest
    </ToolbarButton>
    <ToolbarButton
      disabled={props.submitting}
      className="ide-toolbar__submit"
      onClick={() => props.postSubmit(context)}
    >
      <Icon name="play" />Submit Solution
    </ToolbarButton>
    <ToolbarItem>
      <select
        disabled={props.submitting}
        value={props.editorLang}
        onChange={ev => props.setEditorLanguage(ev.target.value)}
      >
        {_.map(languageEnum.LANG_TEXTS, (val, key) => (
          <option value={key} key={key}>{val}</option>
        ))}
      </select>
    </ToolbarItem>
    <ToolbarSplit />
    <ToolbarButton
      activated={props.pretestVisible}
      onClick={() => props.togglePanel('pretest')}
    >
      <Icon name="edit" />Pretest
    </ToolbarButton>
    <ToolbarButton
      activated={props.recordsVisible}
      onClick={() => props.togglePanel('records')}
    >
      <Icon name="flag" />Records
    </ToolbarButton>
  </Toolbar>
);

IdeToolbarContainer.contextTypes = {
  store: React.PropTypes.object,
};

const mapStateToProps = (state) => ({
  pretestVisible: state.ui.pretest.visible,
  recordsVisible: state.ui.records.visible,
  submitting: state.ui.submitting,
  editorLang: state.editor.lang,
  pretestValid: state.pretest.valid,
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
      .filter(tabId => {
        const item = pretest.items[tabId];
        return item.input.trim().length > 0 && item.output.trim().length > 0;
      });
    // const titles = testCases.map(tabId => pretest.items[tabId].title);
    const inputs = testCases.map(tabId => pretest.items[tabId].input);
    const outputs = testCases.map(tabId => pretest.items[tabId].output);
    const req = util.post(Context.pretestUrl, {
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
    const req = util.post(Context.submitUrl, {
      lang: state.editor.lang,
      code: state.editor.code,
    });
    dispatch({
      type: 'IDE_POST_SUBMIT',
      payload: req,
    });
  },
});

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(IdeToolbarContainer);

