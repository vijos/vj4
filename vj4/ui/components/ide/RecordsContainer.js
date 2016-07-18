import React from 'react';
import { connect } from 'react-redux';
import Pane from './PaneComponent';
import PaneButton from './PaneButtonComponent';

import Tabs, { TabPane } from 'rc-tabs';

const RecordsContainer = (props) => (
  <Pane
    title={<span><span className="icon icon-flag"></span> Records</span>}
  >
    <Tabs
      className="ide-pane-tab"
      activeKey={"all"}
      animation="slide-horizontal"
      tabBarExtraContent={
        <span>
          <PaneButton onClick={props.handleClickClose}><span className="icon icon-close"></span></PaneButton>
        </span>
      }
    >
      <TabPane tab={<span>All</span>} key="all">
        Hello World!
      </TabPane>
    </Tabs>
  </Pane>
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

