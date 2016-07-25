import _ from 'lodash';
import React from 'react';
import { connect } from 'react-redux';
import Icon from './IconComponent';
import Toolbar, {
  ToolbarItemComponent as ToolbarItem,
  ToolbarButtonComponent as ToolbarButton,
  ToolbarSplitComponent as ToolbarSplit,
} from './ToolbarComponent';

import * as languageEnum from '../../../constant/language';

const IdeToolbarContainer = (props) => (
  <Toolbar>
    <ToolbarButton className="ide-toolbar__pretest">
      <Icon name="debug" />Run Pretest
    </ToolbarButton>
    <ToolbarButton className="ide-toolbar__submit">
      <Icon name="play" />Submit Solution
    </ToolbarButton>
    <ToolbarItem>
      <select value={props.editorLang} onChange={ev => props.setEditorLanguage(ev.target.value)}>
        {_.map(languageEnum.LANG_TEXTS, (val, key) => (
          <option value={key} key={key}>{val}</option>
        ))}
      </select>
    </ToolbarItem>
    <ToolbarSplit />
    <ToolbarButton activated={props.pretestVisible} onClick={() => props.togglePanel('pretest')}>
      <Icon name="edit" />Pretest
    </ToolbarButton>
    <ToolbarButton activated={props.recordsVisible} onClick={() => props.togglePanel('records')}>
      <Icon name="flag" />Records
    </ToolbarButton>
  </Toolbar>
);

const mapStateToProps = (state) => ({
  pretestVisible: state.ui.pretest.visible,
  recordsVisible: state.ui.records.visible,
  editorLang: state.editor.lang,
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
});

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(IdeToolbarContainer);

