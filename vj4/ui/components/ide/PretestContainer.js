import React from 'react';
import { connect } from 'react-redux';
import Panel from './PanelComponent';
import PanelButton from './PanelButtonComponent';
import PretestDataInput from './PretestDataInputComponent';

import Tabs, { TabPane } from 'rc-tabs';

const PretestContainer = (props) => (
  <Panel
    title={<span><span className="icon icon-edit"></span> Pretest</span>}
  >
    <Tabs
      className="ide-panel-tab flex-col flex-fill"
      activeKey={props.current}
      onChange={props.handleSwitchData}
      animation="slide-horizontal"
      tabBarExtraContent={
        <span>
          <PanelButton data-tooltip="Add Data" onClick={props.handleClickAdd}>Add</PanelButton>
          <PanelButton data-tooltip="Remove Data" onClick={props.handleClickRemove}>Remove</PanelButton>
          <PanelButton onClick={props.handleClickClose}><span className="icon icon-close"></span></PanelButton>
        </span>
      }
    >
      {props.tabs.map(id => {
        const item = props.items[id];
        return (
          <TabPane tab={item.title} key={id}><div className="flex-row flex-fill">
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
  </Panel>
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

