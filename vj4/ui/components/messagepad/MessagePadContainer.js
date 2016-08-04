import React from 'react';
import { connect } from 'react-redux';
import MessagePadDialogueList from './MessagePadDialogueListContainer';
import MessagePadDialogueContent from './MessagePadDialogueContentContainer';

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
  componentDidMount() {
    this.props.loadDialogues();
  }
  render() {
    return (
      <div className="messagepad clearfix">
        <div className="messagepad__sidebar">
          <div className="section__header">
            <h1 className="section__title">Messages</h1>
            <div className="section__tools"><button type="button" className="tool-button"><span className="icon icon-add"></span> New</button></div>
          </div>
          <MessagePadDialogueList />
        </div>
        <MessagePadDialogueContent />
      </div>
    );
  }
}
