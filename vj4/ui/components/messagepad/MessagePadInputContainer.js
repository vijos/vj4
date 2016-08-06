import React from 'react';
import { connect } from 'react-redux';
import classNames from 'classnames';
import Icon from '../react/IconComponent';

import * as util from '../../misc/Util';

const mapStateToProps = (state) => ({
  activeId: state.activeId,
  isPosting: state.activeId !== null
    ? state.isPosting[state.activeId]
    : false,
  inputValue: state.activeId !== null
    ? state.inputs[state.activeId]
    : '',
});

const mapDispatchToProps = (dispatch) => ({
  handleChange(id, value) {
    dispatch({
      type: 'DIALOGUES_INPUT_CHANGED',
      payload: value,
      meta: {
        dialogueId: id,
      },
    });
  },
  postReply(id, value) {
    if (id === null) {
      return;
    }
    const req = util.post('', {
      operation: 'reply_message',
      message_id: id,
      content: value,
    });
    dispatch({
      type: 'DIALOGUES_POST_REPLY',
      payload: req,
      meta: {
        dialogueId: id,
      },
    });
  },
});

@connect(mapStateToProps, mapDispatchToProps)
export default class MessagePadInputContainer extends React.PureComponent {
  submit() {
    this.props.postReply(this.props.activeId, this.props.inputValue);
  }

  handleKeyDown(ev) {
    if (ev.keyCode === 13 && (ev.ctrlKey || ev.metaKey)) {
      this.submit();
    }
  }

  render() {
    const cn = classNames('messagepad__input', {
      visible: this.props.activeId !== null,
    });
    return (
      <div className={cn}>
        <div className="messagepad__textarea-container">
          <textarea
            ref="input"
            disabled={this.props.isPosting}
            value={this.props.inputValue}
            onKeyDown={ev => this.handleKeyDown(ev)}
            onChange={ev => this.props.handleChange(this.props.activeId, ev.target.value)}
          />
        </div>
        <button
          disabled={!this.props.inputValue.trim().length || this.props.isPosting}
          onClick={() => this.submit()}
        >
          <Icon name="send" />
        </button>
      </div>
    );
  }

  componentWillUpdate(nextProps) {
    this.focusInput = (
      nextProps.activeId !== this.props.activeId
      || this.props.isPosting !== nextProps.isPosting && nextProps.isPosting === false
    );
  }

  componentDidUpdate() {
    if (this.focusInput) {
      this.refs.input.focus();
    }
  }
}
