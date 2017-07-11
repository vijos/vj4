import React from 'react';
import classNames from 'classnames';

export default function DialogueListItemComponent(props) {
  const {
    userName,
    summary,
    faceUrl,
    active,
    onClick,
    className,
    ...rest
  } = props;
  const cn = classNames(className, 'messagepad__list-item media', {
    active,
  });
  return (
    <li {...rest}>
      <a className={cn} onClick={onClick}>
        <div className="media__left middle">
          <img src={faceUrl} alt="avatar" width="50" height="50" className="medium user-profile-avatar" />
        </div>
        <div className="media__body middle">
          <h3 className="messagepad__username">{userName}</h3>
          <div className="messagepad__desc">{summary}</div>
        </div>
      </a>
    </li>
  );
}

DialogueListItemComponent.propTypes = {
  userName: React.PropTypes.string.isRequired,
  summary: React.PropTypes.string.isRequired,
  faceUrl: React.PropTypes.string.isRequired,
  active: React.PropTypes.bool,
  onClick: React.PropTypes.func,
  className: React.PropTypes.string,
};
