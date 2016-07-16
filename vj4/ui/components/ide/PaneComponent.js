import React from 'react';

const PaneComponent = (props) => (
  <div className="ide-pane">
    <div className="ide-pane__title">{props.title}</div>
    <div className="ide-pane__content">{props.children}</div>
  </div>
);

export default PaneComponent;
