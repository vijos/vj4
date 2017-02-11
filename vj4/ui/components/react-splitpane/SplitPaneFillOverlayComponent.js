import React from 'react';
import classNames from 'classnames';

export default function SplitPaneFillOverlayComponent(props) {
  const {
    className,
    children,
    ...rest
  } = props;
  const cn = classNames(className, 'splitpane-fill');
  return (
    <div {...rest} className={cn}>{children}</div>
  );
}

SplitPaneFillOverlayComponent.propTypes = {
  className: React.PropTypes.string,
  children: React.PropTypes.node,
};
