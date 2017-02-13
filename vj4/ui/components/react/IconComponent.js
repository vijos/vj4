import React from 'react';
import classNames from 'classnames';

export default function IconComponent(props) {
  const {
    name,
    className,
    ...rest
  } = props;
  const cn = classNames(className, `icon icon-${name}`);
  return (
    <span {...rest} className={cn} />
  );
}

IconComponent.propTypes = {
  name: React.PropTypes.string.isRequired,
  className: React.PropTypes.string,
};
