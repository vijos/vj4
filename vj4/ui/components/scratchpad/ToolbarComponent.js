import React from 'react';
import classNames from 'classnames';

export default function ToolbarComponent(props) {
  const {
    className,
    children,
    ...rest
  } = props;
  const cn = classNames(className, 'scratchpad__toolbar flex-row flex-cross-center');
  return (
    <div {...rest} className={cn}>{children}</div>
  );
}

ToolbarComponent.propTypes = {
  className: React.PropTypes.string,
  children: React.PropTypes.node,
};

export function ToolbarButtonComponent(props) {
  const {
    activated,
    disabled,
    onClick,
    className,
    children,
    ...rest
  } = props;
  const cn = classNames(className, 'scratchpad__toolbar__item scratchpad__toolbar__button', {
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
      <div>{children}</div>
    </button>
  );
}

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

export function ToolbarSplitComponent(props) {
  const {
    className,
    ...rest
  } = props;
  const cn = classNames(className, 'scratchpad__toolbar__item scratchpad__toolbar__split');
  return (
    <div {...rest} className={cn} />
  );
}

ToolbarSplitComponent.propTypes = {
  className: React.PropTypes.string,
};

export function ToolbarItemComponent(props) {
  const {
    className,
    children,
    ...rest
  } = props;
  const cn = classNames(className, 'scratchpad__toolbar__item');
  return (
    <div {...rest} className={cn}>{children}</div>
  );
}

ToolbarItemComponent.propTypes = {
  className: React.PropTypes.string,
  children: React.PropTypes.node,
};
