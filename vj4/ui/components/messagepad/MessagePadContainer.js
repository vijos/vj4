import React from 'react';
import { connect } from 'react-redux';
import MessagePadDialogueList from './MessagePadDialogueListContainer';
import MessagePadDialogueContent from './MessagePadDialogueContentContainer';
import 'jquery.easing';

import * as util from '../../misc/Util';

const mapDispatchToProps = (dispatch) => ({
  loadDialogues() {
    dispatch({
      type: 'DIALOGUES_LOAD_DIALOGUES',
      payload: util.get(''),
    });
  },
});

@connect(null, mapDispatchToProps)
export default class IdeContainer extends React.PureComponent {
  handleSwitch() {
    const BOUND_TOP = 60;
    const BOUND_BOTTOM = 20;
    const node = this.refs.container;
    if (node.offsetHeight + BOUND_TOP + BOUND_BOTTOM < window.innerHeight) {
      const rect = node.getBoundingClientRect();
      let targetScrollTop = null;
      if (rect.top < BOUND_TOP) {
        targetScrollTop = node.offsetTop - BOUND_TOP;
      } else if (rect.top + node.offsetHeight > window.innerHeight) {
        targetScrollTop = node.offsetTop + node.offsetHeight + BOUND_BOTTOM - window.innerHeight;
      }
      if (targetScrollTop !== null) {
        $('html, body').stop().animate({ scrollTop: targetScrollTop }, 200, 'easeOutCubic');
      }
    }
  }
  componentDidMount() {
    this.props.loadDialogues();
  }
  render() {
    return (
      <div className="messagepad clearfix" ref="container">
        <div className="messagepad__sidebar">
          <div className="section__header">
            <h1 className="section__title">Messages</h1>
            <div className="section__tools"><button type="button" className="tool-button"><span className="icon icon-add"></span> New</button></div>
          </div>
          <MessagePadDialogueList onSwitch={() => this.handleSwitch()} />
        </div>
        <MessagePadDialogueContent />
      </div>
    );
  }
}
