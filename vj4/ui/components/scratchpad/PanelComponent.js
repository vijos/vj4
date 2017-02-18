import React from 'react';
import classNames from 'classnames';
import SplitPaneFillOverlay from 'vj/components/react-splitpane/SplitPaneFillOverlayComponent';

export default function PanelComponent(props) {
  const {
    title,
    className,
    children,
    ...rest
  } = props;
  const cn = classNames(className, 'flex-col');
  return (
    <SplitPaneFillOverlay {...rest} className={cn}>
      <div className="scratchpad__panel-title">{title}</div>
      <div className="flex-col flex-fill">{children}</div>
    </SplitPaneFillOverlay>
  );
}

PanelComponent.propTypes = {
  title: React.PropTypes.node,
  className: React.PropTypes.string,
  children: React.PropTypes.node,
};
