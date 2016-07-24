import React from 'react';
import SplitPane from 'react-split-pane';
import { connect } from 'react-redux';
import _ from 'lodash';
import Overlay from './OverlayComponent';
import IdeToolbar from './IdeToolbarContainer';
import IdeEditor from './IdeEditorContainer';
import IdePretest from './IdePretestContainer';
import IdeRecords from './IdeRecordsContainer';

/*
a: React.Component
panes: [{
  id: string,
  element: React.Component,
  props: {
    visible: bool,
    size: string|int,
  },
}]
*/
function buildNestedPane([a, ...panes]) {
  const elements = [
    a,
    ...panes.filter(p => p.props.visible),
  ];
  if (elements.length === 1) {
    return a;
  }
  return elements
    .reduce((prev, curr) => (
      <SplitPane
        split="horizontal"
        primary="second"
        defaultSize={curr.props.size}
        key={curr.element.key}
        onChange={curr.onChange}
      >
        {prev}
        {curr.element}
      </SplitPane>
    ));
}

const IdeContainer = (props) => (
  <SplitPane
    defaultSize={props.ui.main.size}
    minSize={250}
    split="vertical"
    primary="second"
    onChange={size => props.handleChangeSize('main', size)}
  >
    <div>Problem Content</div>
    {buildNestedPane([
      <Overlay key="editor" className="flex-col flex-fill">
        <IdeToolbar />
        <IdeEditor />
      </Overlay>,
      {
        props: props.ui.pretest,
        onChange: size => props.handleChangeSize('pretest', size),
        element: <IdePretest key="pretest" />,
      },
      {
        props: props.ui.records,
        onChange: size => props.handleChangeSize('records', size),
        element: <IdeRecords key="records" />,
      },
    ])}
  </SplitPane>
);

const mapStateToProps = (state) => ({
  ui: state.ui,
});

const mapDispatchToProps = (dispatch) => ({
  handleChangeSize: _.debounce((uiElement, size) => {
    dispatch({
      type: 'IDE_UI_CHANGE_SIZE',
      payload: {
        uiElement,
        size,
      },
    });
  }, 500),
});

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(IdeContainer);

