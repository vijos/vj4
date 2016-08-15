import React from 'react';
import { connect } from 'react-redux';
import Tabs, { TabPane } from 'rc-tabs';
import Icon from '../react/IconComponent';
import Panel from './PanelComponent';
import PanelButton from './PanelButtonComponent';
import ScratchpadRecordsTable from './ScratchpadRecordsTableContainer';

import i18n from '../../utils/i18n';
import * as util from '../../misc/Util';

const mapDispatchToProps = (dispatch) => ({
  loadSubmissions() {
    dispatch({
      type: 'SCRATCHPAD_RECORDS_LOAD_SUBMISSIONS',
      payload: util.get(Context.getSubmissionsUrl),
    });
  },
  handleClickClose() {
    dispatch({
      type: 'SCRATCHPAD_UI_SET_VISIBILITY',
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
export default class ScratchpadRecordsContainer extends React.PureComponent {
  render() {
    return (
      <Panel
        title={<span><Icon name="flag" /> {i18n('Records')}</span>}
      >
        <Tabs
          className="scratchpad__panel-tab flex-col flex-fill"
          activeKey={"all"}
          animation="slide-horizontal"
          tabBarExtraContent={
            <span>
              <PanelButton
                data-tooltip={i18n('Refresh Records')}
                data-tooltip-below
                onClick={() => this.props.handleClickRefresh()}
              >
                {i18n('Refresh')}
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
            <ScratchpadRecordsTable />
          </TabPane>
        </Tabs>
      </Panel>
    );
  }
  componentDidMount() {
    this.props.loadSubmissions();
  }
}
