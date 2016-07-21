import React from 'react';

const OverlayComponent = (props) => {
  let className = 'ide-overlay';
  if (props.className) {
    className += ` ${props.className}`;
  }
  return (
    <div className={className}>
      {props.children}
    </div>
  );
};

OverlayComponent.propTypes = {
  children: React.PropTypes.node,
  className: React.PropTypes.string,
};

export default OverlayComponent;
