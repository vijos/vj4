import React from 'react';
import classNames from 'classnames';

export default function PanelButtonComponent(props) {
  const {
    className,
    children,
    ...rest
  } = props;
  const cn = classNames(className, 'scratchpad__panel-button');
  return (
    <button {...rest} className={cn}>{children}</button>
  );
}

PanelButtonComponent.propTypes = {
  className: React.PropTypes.string,
  children: React.PropTypes.node,
};
