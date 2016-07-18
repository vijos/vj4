import React from 'react';
import { connect } from 'react-redux';
import Pane from './PaneComponent';
import PaneButton from './PaneButtonComponent';

import Tabs, { TabPane } from 'rc-tabs';

const PretestContainer = (props) => (
  <Pane
    title={<span><span className="icon icon-edit"></span> Pretest</span>}
  >
    <Tabs
      className="ide-pane-tab"
      activeKey={props.current}
      onChange={props.onSwitchData}
      tabBarExtraContent={
        <span>
          <PaneButton data-tooltip="Add Data" onClick={props.onClickAdd}>Add</PaneButton>
          <PaneButton data-tooltip="Remove Data" onClick={props.onClickRemove}>Remove</PaneButton>
          <PaneButton onClick={props.onClickClose}><span className="icon icon-close"></span></PaneButton>
        </span>
      }
    >
      {props.items.map(item => (
        <TabPane tab={item.title} key={item.id}>
          Content {item.id}
        </TabPane>
      ))}
    </Tabs>
  </Pane>
);

const mapStateToProps = (state) => ({
  current: state.pretest.current,
  items: state.pretest.items,
});

const mapDispatchToProps = (dispatch) => ({
  onClickAdd() {
    dispatch({
      type: 'IDE_PRETEST_ADD_DATA',
    });
  },
  onClickRemove() {
    dispatch({
      type: 'IDE_PRETEST_REMOVE_DATA',
    });
  },
  onSwitchData(id) {
    dispatch({
      type: 'IDE_PRETEST_SWITCH_TO_DATA',
      payload: id,
    });
  },
  onClickClose() {
    dispatch({
      type: 'IDE_UI_SET_VISIBILITY',
      payload: {
        uiElement: 'pretest',
        visibility: false,
      },
    });
  },
});

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(PretestContainer);
