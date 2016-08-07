import React from 'react';
import _ from 'lodash';
import { connect } from 'react-redux';
import Icon from '../react/IconComponent';
import MessagePadDialogueList from './MessagePadDialogueListContainer';
import MessagePadDialogueContent from './MessagePadDialogueContentContainer';
import MessagePadInput from './MessagePadInputContainer';
import 'jquery.easing';

import * as util from '../../misc/Util';

const mapDispatchToProps = (dispatch) => ({
  loadDialogues() {
    dispatch({
      type: 'DIALOGUES_LOAD_DIALOGUES',
      payload: util.get(''),
    });
  },
  handleNewDialogue() {
    // TODO: pop up a dialog and pass udoc to store
    const uid = parseInt(prompt('UID'), 10);
    if (isNaN(uid)) {
      return;
    }
    if (uid === UserContext.uid) {
      return;
    }
    dispatch({
      type: 'DIALOGUES_CREATE',
      payload: {
        id: _.uniqueId('PLACEHOLDER_'),
        uid,
      },
    });
  },
});

@connect(null, mapDispatchToProps)
export default class MessagePadContainer extends React.PureComponent {
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
  render() {
    return (
      <div className="messagepad clearfix" ref="container">
        <div className="messagepad__sidebar">
          <div className="section__header">
            <h1 className="section__title">Messages</h1>
            <div className="section__tools">
              <button
                onClick={() => this.props.handleNewDialogue()}
                className="tool-button"
              >
                <Icon name="add" /> New
              </button>
            </div>
          </div>
          <MessagePadDialogueList onSwitch={() => this.handleSwitch()} />
        </div>
        <MessagePadDialogueContent />
        <MessagePadInput />
      </div>
    );
  }
  componentDidMount() {
    this.props.loadDialogues();
  }
}
