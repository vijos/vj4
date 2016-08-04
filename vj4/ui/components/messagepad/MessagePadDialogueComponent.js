import React from 'react';
import classNames from 'classnames';

export default function MessagePadDialogueComponent(props) {
  const {
    faceUrl,
    isSelf,
    className,
    children,
    ...rest,
  } = props;
  const cn = classNames(className, 'messagepad__dialogue-container', {
    'side--self': isSelf,
    'side--other': !isSelf,
  });
  return (
    <li {...rest} className={cn}>
      <div className="messagepad__dialogue__avatar">
        <img src={faceUrl} width="50" height="50" className="medium user-profile-avatar" />
      </div>
      <div className="messagepad__dialogue__msg">
        {children}
      </div>
    </li>
  );
}

MessagePadDialogueComponent.propTypes = {
  isSelf: React.PropTypes.bool,
  faceUrl: React.PropTypes.string.isRequired,
  className: React.PropTypes.string,
  children: React.PropTypes.node,
};
