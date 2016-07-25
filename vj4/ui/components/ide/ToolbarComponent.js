import React from 'react';
import classNames from 'classnames';

const ToolbarComponent = (props) => {
  const {
    className,
    children,
    ...rest,
  } = props;
  const cn = classNames(className, 'ide-toolbar flex-row flex-cross-center');
  return (
    <div {...rest} className={cn}>{children}</div>
  );
};

ToolbarComponent.propTypes = {
  className: React.PropTypes.string,
  children: React.PropTypes.node,
};

export default ToolbarComponent;

export const ToolbarButtonComponent = (props) => {
  const {
    activated,
    disabled,
    onClick,
    className,
    children,
    ...rest,
  } = props;
  const cn = classNames(className, 'ide-toolbar__item ide-toolbar__button', {
    activated,
    disabled,
    enabled: !disabled,
  });
  return (
    <button
      {...rest}
      tabIndex="-1"
      className={cn}
      onClick={() => !disabled && onClick && onClick()}
    >
      {children}
    </button>
  );
};

ToolbarButtonComponent.propTypes = {
  activated: React.PropTypes.bool,
  disabled: React.PropTypes.bool,
  onClick: React.PropTypes.func,
  className: React.PropTypes.string,
  children: React.PropTypes.node,
};

ToolbarButtonComponent.defaultProps = {
  activated: false,
  disabled: false,
};

export const ToolbarSplitComponent = (props) => {
  const {
    className,
    ...rest,
  } = props;
  const cn = classNames(className, 'ide-toolbar__item ide-toolbar__split');
  return (
    <div {...rest} className={cn} />
  );
};

ToolbarSplitComponent.propTypes = {
  className: React.PropTypes.string,
};

export const ToolbarItemComponent = (props) => {
  const {
    className,
    children,
    ...rest,
  } = props;
  const cn = classNames(className, 'ide-toolbar__item');
  return (
    <div {...rest} className={cn}>{children}</div>
  );
};

ToolbarItemComponent.propTypes = {
  className: React.PropTypes.string,
  children: React.PropTypes.node,
};
