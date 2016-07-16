import React from 'react';
import SplitPane from 'react-split-pane';
import { connect } from 'react-redux';
import _ from 'lodash';
import IdeEditor from './EditorContainer';
import IdePretest from './PretestContainer';
import IdeRecords from './RecordsContainer';

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
    onChange={size => props.onChangeSize('main', size)}
  >
    <div>Problem Content</div>
    {buildNestedPane([
      <IdeEditor key="editor" />,
      {
        props: props.ui.pretest,
        onChange: size => props.onChangeSize('pretest', size),
        element: <IdePretest key="pretest" />,
      },
      {
        props: props.ui.records,
        onChange: size => props.onChangeSize('records', size),
        element: <IdeRecords key="records" />,
      },
    ])}
  </SplitPane>
);

const mapStateToProps = (state) => ({
  ui: state.ui,
});

const mapDispatchToProps = (dispatch) => ({
  onChangeSize: _.debounce((uiElement, size) => {
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
