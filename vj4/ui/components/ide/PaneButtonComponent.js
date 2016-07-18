import React from 'react';

const PaneButtonComponent = (props) => (
  <button className="ide-pane-button" {...props}>
    {props.children}
  </button>
);

PaneButtonComponent.propTypes = {
  children: React.PropTypes.node,
};

export default PaneButtonComponent;
