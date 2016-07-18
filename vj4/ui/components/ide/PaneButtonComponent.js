import React from 'react';

const PaneButtonComponent = (props) => (
  <button className="ide-pane-button" {...props}>
    {props.children}
  </button>
);

export default PaneButtonComponent;
