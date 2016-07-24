import React from 'react';
import classNames from 'classnames';

const PanelButtonComponent = (props) => {
  const {
    className,
    children,
    ...rest,
  } = props;
  const cn = classNames(className, 'ide-panel-button');
  return (
    <button {...rest} className={cn}>{children}</button>
  );
};

PanelButtonComponent.propTypes = {
  className: React.PropTypes.string,
  children: React.PropTypes.node,
};

export default PanelButtonComponent;
