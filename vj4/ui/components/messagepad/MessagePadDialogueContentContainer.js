import React from 'react';
import _ from 'lodash';
import { connect } from 'react-redux';
import TimeAgo from 'timeago-react';
import moment from 'moment';
import 'jquery-scroll-lock';
import 'jquery.easing';

import i18n from 'vj/utils/i18n';
import Message from './MessageComponent';

const mapStateToProps = state => ({
  activeId: state.activeId,
  item: state.activeId !== null
    ? state.dialogues[state.activeId]
    : null,
});

@connect(mapStateToProps, null)
export default class MessagePadDialogueContentContainer extends React.PureComponent {
  componentDidMount() {
    $(this.refs.list).scrollLock({ strict: true });
  }

  componentDidUpdate(prevProps) {
    const node = this.refs.list;
    if (this.props.activeId !== prevProps.activeId) {
      this.scrollToBottom = true;
      this.scrollWithAnimation = false;
    } else if (node.scrollTop + node.offsetHeight === node.scrollHeight) {
      this.scrollToBottom = true;
      this.scrollWithAnimation = true;
    } else {
      this.scrollToBottom = false;
    }

    if (this.scrollToBottom) {
      const targetScrollTop = node.scrollHeight - node.offsetHeight;
      if (this.scrollWithAnimation) {
        $(node).stop().animate({ scrollTop: targetScrollTop }, 200, 'easeOutCubic');
      } else {
        node.scrollTop = targetScrollTop;
      }
    }
  }

  renderInner() {
    if (this.props.activeId === null) {
      return [];
    }
    return _.map(this.props.item.reply, (reply, idx) => (
      <Message
        key={idx}
        isSelf={reply.sender_uid === UserContext.uid}
        faceUrl={
          reply.sender_uid === this.props.item.sender_uid
            ? this.props.item.sender_udoc.gravatar_url
            : this.props.item.sendee_udoc.gravatar_url
        }
      >
        <div>{reply.content}</div>
        <time data-tooltip={moment(reply.at).format('YYYY-MM-DD HH:mm:ss')}>
          <TimeAgo datetime={reply.at} locale={i18n('timeago_locale')} />
        </time>
      </Message>
    ));
  }

  render() {
    return (
      <ol className="messagepad__content" ref="list">
        {this.renderInner()}
      </ol>
    );
  }
}
