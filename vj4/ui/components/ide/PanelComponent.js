import React from 'react';
import classNames from 'classnames';

const PanelComponent = (props) => {
  const {
    title,
    className,
    children,
    ...rest,
  } = props;
  const cn = classNames(className, 'flex-col flex-fill');
  return (
    <div {...rest} className={cn}>
      <div className="ide-panel-title">{props.title}</div>
      <div className="flex-col flex-fill">{props.children}</div>
    </div>
  );
};

PanelComponent.propTypes = {
  title: React.PropTypes.node,
  className: React.PropTypes.string,
  children: React.PropTypes.node,
};

export default PanelComponent;
