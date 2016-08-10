import React from 'react';
import { connect } from 'react-redux';
import Tabs, { TabPane } from 'rc-tabs';
import Icon from '../react/IconComponent';
import Panel from './PanelComponent';
import PanelButton from './PanelButtonComponent';
import ScratchpadPretestTabPane from './ScratchpadPretestTabPaneContainer';

const mapStateToProps = (state) => ({
  current: state.pretest.current,
  tabs: state.pretest.tabs,
  meta: state.pretest.meta,
});

const mapDispatchToProps = (dispatch) => ({
  handleClickAdd() {
    dispatch({
      type: 'SCRATCHPAD_PRETEST_ADD_DATA',
    });
  },
  handleClickRemove() {
    dispatch({
      type: 'SCRATCHPAD_PRETEST_REMOVE_DATA',
    });
  },
  handleSwitchData(id) {
    dispatch({
      type: 'SCRATCHPAD_PRETEST_SWITCH_TO_DATA',
      payload: id,
    });
  },
  handleClickClose() {
    dispatch({
      type: 'SCRATCHPAD_UI_SET_VISIBILITY',
      payload: {
        uiElement: 'pretest',
        visibility: false,
      },
    });
  },
});

@connect(mapStateToProps, mapDispatchToProps)
export default class ScratchpadPretestContainer extends React.PureComponent {
  render() {
    return (
      <Panel
        title={<span><Icon name="edit" /> Pretest</span>}
      >
        <Tabs
          className="scratchpad__panel-tab flex-col flex-fill"
          activeKey={this.props.current}
          onChange={tabId => this.props.handleSwitchData(tabId)}
          animation="slide-horizontal"
          tabBarExtraContent={
            <span>
              <PanelButton
                data-tooltip="Add Data"
                onClick={() => this.props.handleClickAdd()}
              >
                Add
              </PanelButton>
              <PanelButton
                data-tooltip="Remove Data"
                onClick={() => this.props.handleClickRemove()}
              >
                Remove
              </PanelButton>
              <PanelButton
                onClick={() => this.props.handleClickClose()}
              >
                <Icon name="close" />
              </PanelButton>
            </span>
          }
        >
          {this.props.tabs.map(tabId => (
            <TabPane tab={this.props.meta[tabId].title} key={tabId}>
              <ScratchpadPretestTabPane id={tabId} />
            </TabPane>
          ))}
        </Tabs>
      </Panel>
    );
  }
}
