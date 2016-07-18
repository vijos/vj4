import React from 'react';

const PaneComponent = (props) => (
  <div className="ide-pane">
    <div className="ide-pane-title">{props.title}</div>
    <div className="ide-pane-content">{props.children}</div>
  </div>
);

export default PaneComponent;
