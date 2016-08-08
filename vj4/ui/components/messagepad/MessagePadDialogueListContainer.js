import React from 'react';
import _ from 'lodash';
import { connect } from 'react-redux';
import ListItem from './DialogueListItemComponent';
import 'jquery-scroll-lock';

const mapStateToProps = (state) => ({
  activeId: state.activeId,
  dialogues: state.dialogues,
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
  handleClick(id) {
    this.props.handleClick(id);
    if (this.props.onSwitch) {
      this.props.onSwitch(id);
    }
  }
  render() {
    const orderedDialogues = _.orderBy(
      _.values(this.props.dialogues),
      dialogue => (dialogue.isPlaceholder
        ? Number.POSITIVE_INFINITY
        : _.maxBy(dialogue.reply, 'at').at),
      'desc'
    );
    return (
      <ol className="messagepad__list" ref="list">
      {_.map(orderedDialogues, dialogue => {
        const udoc = dialogue.sendee_uid !== UserContext.uid ? dialogue.sendee_udoc : dialogue.sender_udoc;
        return (
          <ListItem
            key={dialogue._id}
            userName={udoc.uname}
            summary={dialogue.isPlaceholder ? '' : _.last(dialogue.reply).content}
            faceUrl="//gravatar.lug.ustc.edu.cn/avatar/3efe6856c336243c907e2852b0498fcf?d=mm&amp;s=200"
            active={dialogue._id === this.props.activeId}
            onClick={() => this.handleClick(dialogue._id)}
          />
        );
      })}
      </ol>
    );
  }
  componentDidMount() {
    $(this.refs.list).scrollLock({ strict: true });
  }
}
