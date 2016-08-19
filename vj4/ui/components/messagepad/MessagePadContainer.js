import React from 'react';
import { connect } from 'react-redux';
import Icon from '../react/IconComponent';
import MessagePadDialogueList from './MessagePadDialogueListContainer';
import MessagePadDialogueContent from './MessagePadDialogueContentContainer';
import MessagePadInput from './MessagePadInputContainer';
import 'jquery.easing';

import * as util from '../../misc/Util';
import i18n from '../../utils/i18n';

const mapDispatchToProps = (dispatch) => ({
  loadDialogues() {
    dispatch({
      type: 'DIALOGUES_LOAD_DIALOGUES',
      payload: util.get(''),
    });
  },
});

@connect(null, mapDispatchToProps)
export default class MessagePadContainer extends React.PureComponent {
  static propTypes = {
    onAdd: React.PropTypes.func.isRequired,
  };
  handleSwitch() {
    const BOUND_TOP = 60;
    const BOUND_BOTTOM = 20;
    const node = this.refs.container;
    if (node.offsetHeight + BOUND_TOP + BOUND_BOTTOM < window.innerHeight) {
      const rect = node.getBoundingClientRect();
      const rectBody = document.body.getBoundingClientRect();
      let targetScrollTop = null;
      if (rect.top < BOUND_TOP) {
        targetScrollTop = rect.top - rectBody.top - BOUND_TOP;
      } else if (rect.top + node.offsetHeight > window.innerHeight) {
        targetScrollTop = rect.top - rectBody.top + node.offsetHeight + BOUND_BOTTOM - window.innerHeight;
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
            <h1 className="section__title">{i18n('Messages')}</h1>
            <div className="section__tools">
              <button
                onClick={() => this.props.onAdd()}
                className="tool-button"
              >
                <Icon name="add" /> {i18n('New')}
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
