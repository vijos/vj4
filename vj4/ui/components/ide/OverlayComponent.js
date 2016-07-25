import React from 'react';
import classNames from 'classnames';

export default function OverlayComponent(props) {
  const {
    className,
    children,
    ...rest,
  } = props;
  const cn = classNames(className, 'ide-overlay');
  return (
    <div {...rest} className={cn}>{children}</div>
  );
}

OverlayComponent.propTypes = {
  className: React.PropTypes.string,
  children: React.PropTypes.node,
};
