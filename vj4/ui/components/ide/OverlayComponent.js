import React from 'react';
import classNames from 'classnames';

const OverlayComponent = (props) => {
  const {
    className,
    children,
    ...rest,
  } = props;
  const cn = classNames(className, 'ide-overlay');
  return (
    <div {...rest} className={cn}>{children}</div>
  );
};

OverlayComponent.propTypes = {
  className: React.PropTypes.string,
  children: React.PropTypes.node,
};

export default OverlayComponent;
