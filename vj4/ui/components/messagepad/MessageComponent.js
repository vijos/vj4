import React from 'react';
import classNames from 'classnames';

export default function MessageComponent(props) {
  const {
    faceUrl,
    isSelf,
    className,
    children,
    ...rest
  } = props;
  const cn = classNames(className, 'messagepad__message', {
    'side--self': isSelf,
    'side--other': !isSelf,
  });
  return (
    <li {...rest} className={cn}>
      <div className="messagepad__message__avatar">
        <img src={faceUrl} alt="avatar" width="50" height="50" className="medium user-profile-avatar" />
      </div>
      <div className="messagepad__message__body">
        {children}
      </div>
    </li>
  );
}

MessageComponent.propTypes = {
  isSelf: React.PropTypes.bool,
  faceUrl: React.PropTypes.string.isRequired,
  className: React.PropTypes.string,
  children: React.PropTypes.node,
};
