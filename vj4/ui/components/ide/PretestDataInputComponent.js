import React from 'react';

const PretestDataInputComponent = (props) => (
  <div className="flex-col flex-fill">
    <textarea
      className="ide-pretest__data-input"
      wrap="off"
      value={props.value}
      onChange={ev => props.onChange(ev.target.value)}
      placeholder={props.title}
    />
  </div>
);

PretestDataInputComponent.propTypes = {
  title: React.PropTypes.node,
  value: React.PropTypes.string,
  onChange: React.PropTypes.func,
};

export default PretestDataInputComponent;
