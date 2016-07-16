import React from 'react';
import { connect } from 'react-redux';
import Pane from './PaneComponent';

import Tabs, { TabPane } from 'rc-tabs';

const RecordsContainer = (props) => (
  <Pane
    title={<span><span className="icon icon-flag"></span>Records</span>}
  >
    <Tabs
      activeKey={"a"}
      tabBarExtraContent={<button>+添加</button>}
    >
      <TabPane
        tab={<span>A</span>}
        key="a"
      >
        Content A
      </TabPane>
      <TabPane
        tab={<span>B</span>}
        key="b"
      >
        Content B
      </TabPane>
      <TabPane
        tab={<span>C</span>}
        key="c"
      >
        Content C
      </TabPane>
    </Tabs>
  </Pane>
);

const mapStateToProps = (state) => ({
});

const mapDispatchToProps = (dispatch) => ({
});

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(RecordsContainer);
