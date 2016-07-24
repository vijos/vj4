import React from 'react';
import { connect } from 'react-redux';
import Icon from './IconComponent';
import Toolbar, {
  ToolbarButtonComponent as ToolbarButton,
  ToolbarSplitComponent as ToolbarSplit,
} from './ToolbarComponent';

const IdeToolbarContainer = (props) => (
  <Toolbar
    extra={
      <span></span>
    }
  >
    <ToolbarButton className="ide-toolbar__pretest">
      <Icon name="debug" />Run Pretest
    </ToolbarButton>
    <ToolbarButton className="ide-toolbar__submit">
      <Icon name="play" />Submit Solution
    </ToolbarButton>
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
});

const mapDispatchToProps = (dispatch) => ({
  togglePanel(uiElement) {
    dispatch({
      type: 'IDE_UI_TOGGLE_VISIBILITY',
      payload: { uiElement },
    });
  },
});

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(IdeToolbarContainer);

