import React from 'react';
import { connect } from 'react-redux';
import Tabs, { TabPane } from 'rc-tabs';
import Icon from './IconComponent';
import Panel from './PanelComponent';
import PanelButton from './PanelButtonComponent';
import IdePretestTabPane from './IdePretestTabPaneContainer';

const mapStateToProps = (state) => ({
  current: state.pretest.current,
  tabs: state.pretest.tabs,
  meta: state.pretest.meta,
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
});

@connect(mapStateToProps, mapDispatchToProps)
export default class IdePretestContainer extends React.Component {
  static propTypes = {
    current: React.PropTypes.string,
    tabs: React.PropTypes.arrayOf(React.PropTypes.string),
    meta: React.PropTypes.arrayOf(React.PropTypes.shape({
      title: React.PropTypes.string,
    })),
    handleClickAdd: React.PropTypes.func,
    handleClickRemove: React.PropTypes.func,
    handleSwitchData: React.PropTypes.func,
    handleClickClose: React.PropTypes.func,
  };
  render() {
    return (
      <Panel
        title={<span><Icon name="edit" /> Pretest</span>}
      >
        <Tabs
          className="ide-panel-tab flex-col flex-fill"
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
              <IdePretestTabPane id={tabId} />
            </TabPane>
          ))}
        </Tabs>
      </Panel>
    );
  }
}
