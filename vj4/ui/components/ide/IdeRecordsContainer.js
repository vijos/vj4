import React from 'react';
import { connect } from 'react-redux';
import Tabs, { TabPane } from 'rc-tabs';
import visualizeRender from '../../utils/visualizeRender';
import Icon from './IconComponent';
import Panel from './PanelComponent';
import PanelButton from './PanelButtonComponent';
import IdeRecordsTable from './IdeRecordsTableContainer';

import * as util from '../../misc/Util';

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
  loadSubmissions() {
    dispatch({
      type: 'IDE_RECORDS_LOAD_SUBMISSIONS',
      payload: util.get(Context.getSubmissionsUrl),
    });
  },
});

@connect(null, mapDispatchToProps)
//@visualizeRender
export default class IdeRecordsContainer extends React.Component {
  componentDidMount() {
    this.props.loadSubmissions();
  }
  render() {
    return (
      <Panel
        title={<span><Icon name="flag" /> Records</span>}
      >
        <Tabs
          className="ide-panel-tab flex-col flex-fill"
          activeKey={"all"}
          animation="slide-horizontal"
          tabBarExtraContent={
            <span>
              <PanelButton
                onClick={this.props.handleClickClose}
              >
                <Icon name="close" />
              </PanelButton>
            </span>
          }
        >
          <TabPane tab={<span>All</span>} key="all">
            <IdeRecordsTable />
          </TabPane>
        </Tabs>
      </Panel>
    );
  }
}
