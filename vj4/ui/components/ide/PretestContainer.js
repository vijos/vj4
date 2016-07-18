import React from 'react';
import { connect } from 'react-redux';
import Pane from './PaneComponent';
import PaneButton from './PaneButtonComponent';
import PretestDataInput from './PretestDataInputComponent';

import Tabs, { TabPane } from 'rc-tabs';

const PretestContainer = (props) => (
  <Pane
    title={<span><span className="icon icon-edit"></span> Pretest</span>}
  >
    <Tabs
      className="ide-pane-tab"
      activeKey={props.current}
      onChange={props.handleSwitchData}
      animation="slide-horizontal"
      tabBarExtraContent={
        <span>
          <PaneButton data-tooltip="Add Data" onClick={props.handleClickAdd}>Add</PaneButton>
          <PaneButton data-tooltip="Remove Data" onClick={props.handleClickRemove}>Remove</PaneButton>
          <PaneButton onClick={props.handleClickClose}><span className="icon icon-close"></span></PaneButton>
        </span>
      }
    >
      {props.tabs.map(id => {
        const item = props.items[id];
        return (
          <TabPane tab={item.title} key={id}><div className="ide-pretest__data-container">
            <PretestDataInput
              title="Sample Input"
              value={item.input}
              onChange={v => props.handleDataChange(id, 'input', v)}
            />
            <PretestDataInput
              title="Sample Output"
              value={item.output}
              onChange={v => props.handleDataChange(id, 'output', v)}
            />
          </div></TabPane>
        );
      })}
    </Tabs>
  </Pane>
);

const mapStateToProps = (state) => ({
  current: state.pretest.current,
  tabs: state.pretest.tabs,
  items: state.pretest.items,
});

const mapDispatchToProps = (dispatch) => ({
  handleClickAdd() {
    dispatch({
      type: 'IDE_PRETEST_ADD_DATA',
    });
  },
  handleClickRemove() {
    dispatch({
      type: 'IDE_PRETEST_REMOVE_DATA',
    });
  },
  handleSwitchData(id) {
    dispatch({
      type: 'IDE_PRETEST_SWITCH_TO_DATA',
      payload: id,
    });
  },
  handleClickClose() {
    dispatch({
      type: 'IDE_UI_SET_VISIBILITY',
      payload: {
        uiElement: 'pretest',
        visibility: false,
      },
    });
  },
  handleDataChange(id, type, value) {
    dispatch({
      type: 'IDE_PRETEST_DATA_CHANGE',
      payload: {
        id,
        type,
        value,
      },
    });
  },
});

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(PretestContainer);

