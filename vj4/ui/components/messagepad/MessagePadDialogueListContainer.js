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
  static propTypes = {
    onSwitch: React.PropTypes.func,
  };

  handleClick(id) {
    this.props.handleClick(id);
    if (this.props.onSwitch) {
      this.props.onSwitch(id);
    }
  }

  render() {
    const orderedDialogues = _.orderBy(
      _.values(this.props.dialogues),
      dialogue => _.maxBy(dialogue.reply, 'at').at,
      'desc'
    );
    _.values(this.props.dialogues).forEach(dialogue => {
      console.log(_.maxBy(dialogue.reply, 'at'));
    });

    return (
      <ol className="messagepad__list" ref="list">
      {_.map(orderedDialogues, dialogue => (
        <ListItem
          key={dialogue._id}
          userName={dialogue.sendee_uid !== UserContext.uid ? dialogue.sendee_uid : dialogue.sender_uid}
          summary={_.last(dialogue.reply).content}
          faceUrl="//gravatar.lug.ustc.edu.cn/avatar/3efe6856c336243c907e2852b0498fcf?d=mm&amp;s=200"
          active={dialogue._id === this.props.activeId}
          onClick={() => this.handleClick(dialogue._id)}
        />
      ))}
      </ol>
    );
  }

  componentDidMount() {
    $(this.refs.list).scrollLock({ strict: true });
  }
}
