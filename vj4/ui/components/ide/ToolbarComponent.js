import React from 'react';

const ToolbarComponent = (props) => (
  <div className="ide-toolbar flex-row flex-cross-center">
    {props.children}
  </div>
);

ToolbarComponent.propTypes = {
  children: React.PropTypes.node,
};

export default ToolbarComponent;
