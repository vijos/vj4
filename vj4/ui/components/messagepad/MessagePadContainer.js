import React from 'react';
import { connect } from 'react-redux';
import Icon from '../react/IconComponent';
import MessagePadDialogueList from './MessagePadDialogueListContainer';
import MessagePadDialogueContent from './MessagePadDialogueContentContainer';
import MessagePadInput from './MessagePadInputContainer';

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
  render() {
    return (
      <div className="messagepad clearfix">
        <div className="messagepad__sidebar">
          <div className="section__header">
            <button
              onClick={() => this.props.onAdd()}
              className="primary rounded button"
            >
              <Icon name="add" /> {i18n('New')}
            </button>
          </div>
          <MessagePadDialogueList />
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
