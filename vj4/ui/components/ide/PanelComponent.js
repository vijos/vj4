import React from 'react';

const PanelComponent = (props) => (
  <div className="flex-col flex-fill">
    <div className="ide-panel-title">{props.title}</div>
    <div className="flex-col flex-fill">{props.children}</div>
  </div>
);

PanelComponent.propTypes = {
  title: React.PropTypes.node,
  children: React.PropTypes.node,
};

export default PanelComponent;
