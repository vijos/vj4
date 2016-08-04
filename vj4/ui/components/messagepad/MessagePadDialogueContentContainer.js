import React from 'react';
import _ from 'lodash';
import { connect } from 'react-redux';
import Dialogue from './MessagePadDialogueComponent';
import moment from 'moment';

const mapStateToProps = (state) => ({
  activeTab: state.dialogue.activeTab,
  item: state.dialogue.activeTab !== null
    ? state.dialogue.items[state.dialogue.activeTab]
    : null,
});

const mapDispatchToProps = (dispatch) => ({
});

@connect(mapStateToProps, mapDispatchToProps)
export default class MessagePadDialogueContentContainer extends React.PureComponent {
  render() {
    return (
      <ol className="messagepad__content">
        {this.renderInner()}
      </ol>
    );
  }

  renderInner() {
    if (this.props.activeTab === null) {
      return [];
    }
    return _.map(this.props.item.reply, (reply, idx) => (
      <Dialogue
        key={idx}
        isSelf={reply.sender_uid === UserContext.uid}
        faceUrl="//gravatar.lug.ustc.edu.cn/avatar/3efe6856c336243c907e2852b0498fcf?d=mm&amp;s=200"
      >
        <div>{reply.content}</div>
        <time>{moment(reply.at).fromNow()}</time>
      </Dialogue>
    ));
  }
}
