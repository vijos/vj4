import React from 'react';
import { connect } from 'react-redux';
import Icon from './IconComponent';
import Panel from './PanelComponent';
import PanelButton from './PanelButtonComponent';

import Tabs, { TabPane } from 'rc-tabs';

const IdeRecordsContainer = (props) => (
  <Panel
    title={<span><Icon name="flag" /> Records</span>}
  >
    <Tabs
      className="ide-panel-tab flex-col flex-fill"
      activeKey={"all"}
      animation="slide-horizontal"
      tabBarExtraContent={
        <span>
          <PanelButton onClick={props.handleClickClose}><Icon name="close" /></PanelButton>
        </span>
      }
    >
      <TabPane tab={<span>All</span>} key="all">
        Hello World!
      </TabPane>
    </Tabs>
  </Panel>
);

const mapStateToProps = (state) => ({
});

const mapDispatchToProps = (dispatch) => ({
  handleClickClose() {
    dispatch({
      type: 'IDE_UI_SET_VISIBILITY',
      payload: {
        uiElement: 'records',
        visibility: false,
      },
    });
  },
});

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(IdeRecordsContainer);
