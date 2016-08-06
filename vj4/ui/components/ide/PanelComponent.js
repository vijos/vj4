import React from 'react';
import classNames from 'classnames';

export default function PanelComponent(props) {
  const {
    title,
    className,
    children,
    ...rest,
  } = props;
  const cn = classNames(className, 'flex-col flex-fill');
  return (
    <div {...rest} className={cn}>
      <div className="ide__panel-title">{title}</div>
      <div className="flex-col flex-fill">{children}</div>
    </div>
  );
}

PanelComponent.propTypes = {
  title: React.PropTypes.node,
  className: React.PropTypes.string,
  children: React.PropTypes.node,
};
