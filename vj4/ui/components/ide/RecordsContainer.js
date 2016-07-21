import React from 'react';
import { connect } from 'react-redux';
import Panel from './PanelComponent';
import PanelButton from './PanelButtonComponent';

import Tabs, { TabPane } from 'rc-tabs';

const RecordsContainer = (props) => (
  <Panel
    title={<span><span className="icon icon-flag"></span> Records</span>}
  >
    <Tabs
      className="ide-panel-tab flex-col flex-fill"
      activeKey={"all"}
      animation="slide-horizontal"
      tabBarExtraContent={
        <span>
          <PanelButton onClick={props.handleClickClose}><span className="icon icon-close"></span></PanelButton>
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
)(RecordsContainer);

