import React from 'react';
import _ from 'lodash';
import { connect } from 'react-redux';
import ListItem from './MessagePadDialogueListItemComponent';

const mapStateToProps = (state) => ({
  items: state.dialogue.items,
  activeTab: state.dialogue.activeTab,
});

const mapDispatchToProps = (dispatch) => ({
  handleClick(id) {
    dispatch({
      type: 'DIALOGUES_SWITCH_TO',
      payload: id,
    });
  },
});

@connect(mapStateToProps, mapDispatchToProps)
export default class MessagePadDialogueListContainer extends React.PureComponent {
  render() {
    const orderedItems = _.orderBy(
      this.props.items,
      dialogue => _.maxBy(dialogue.reply, reply => new Date(reply.at).getTime()),
      'desc'
    );
    return (
      <ol className="messagepad__list">
      {_.map(orderedItems, item => (
        <ListItem
          key={item._id}
          userName={item.sendee_uid !== UserContext.uid ? item.sendee_uid : item.sender_uid}
          summary={_.last(item.reply).content}
          faceUrl="//gravatar.lug.ustc.edu.cn/avatar/3efe6856c336243c907e2852b0498fcf?d=mm&amp;s=200"
          active={item._id === this.props.activeTab}
          onClick={() => this.props.handleClick(item._id)}
        />
      ))}
      </ol>
    );
  }
}
