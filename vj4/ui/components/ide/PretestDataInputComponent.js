import React from 'react';

const PretestDataInputComponent = (props) => (
  <div className="ide-pretest__data">
    <textarea
      className="ide-pretest__data-input"
      wrap="off"
      value={props.value}
      onChange={ev => props.onChange(ev.target.value)}
    />
    <div className="ide-pretest__data-name">{props.title}</div>
  </div>
);

PretestDataInputComponent.propTypes = {
  title: React.PropTypes.node,
  value: React.PropTypes.string,
  onChange: React.PropTypes.func,
};

export default PretestDataInputComponent;
