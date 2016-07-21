import React from 'react';

const PanelButtonComponent = (props) => (
  <button className="ide-panel-button" {...props}>
    {props.children}
  </button>
);

PanelButtonComponent.propTypes = {
  children: React.PropTypes.node,
};

export default PanelButtonComponent;
