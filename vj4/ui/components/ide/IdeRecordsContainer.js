import React from 'react';
import { connect } from 'react-redux';
import Tabs, { TabPane } from 'rc-tabs';
import Icon from '../react/IconComponent';
import Panel from './PanelComponent';
import PanelButton from './PanelButtonComponent';
import IdeRecordsTable from './IdeRecordsTableContainer';

import * as util from '../../misc/Util';

const mapDispatchToProps = (dispatch) => ({
  loadSubmissions() {
    dispatch({
      type: 'IDE_RECORDS_LOAD_SUBMISSIONS',
      payload: util.get(Context.getSubmissionsUrl),
    });
  },
  handleClickClose() {
    dispatch({
      type: 'IDE_UI_SET_VISIBILITY',
      payload: {
        uiElement: 'records',
        visibility: false,
      },
    });
  },
  handleClickRefresh() {
    this.loadSubmissions();
  },
});

@connect(null, mapDispatchToProps)
export default class IdeRecordsContainer extends React.PureComponent {
  static propTypes = {
    loadSubmissions: React.PropTypes.func,
    handleClickClose: React.PropTypes.func,
    handleClickRefresh: React.PropTypes.func,
  };
  componentDidMount() {
    this.props.loadSubmissions();
  }
  render() {
    return (
      <Panel
        title={<span><Icon name="flag" /> Records</span>}
      >
        <Tabs
          className="ide__panel-tab flex-col flex-fill"
          activeKey={"all"}
          animation="slide-horizontal"
          tabBarExtraContent={
            <span>
              <PanelButton
                data-tooltip="Refresh Records"
                onClick={() => this.props.handleClickRefresh()}
              >
                Refresh
              </PanelButton>
              <PanelButton
                onClick={() => this.props.handleClickClose()}
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
