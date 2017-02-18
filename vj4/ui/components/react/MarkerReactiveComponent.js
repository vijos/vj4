import React from 'react';
import classNames from 'classnames';
import MarkerReactive from 'vj/components/marker/MarkerReactive';

export default class MarkerReactiveComponent extends React.PureComponent {
  componentDidMount() {
    this.marker = MarkerReactive.initFromDOM($(this.refs.dom));
  }
  componentWillUnmount() {
    // in fact this will not be called since we use fadeOut?
    this.marker.detach();
  }
  render() {
    const {
      children,
      ...rest
    } = this.props;
    return (
      <div {...rest} ref="dom">{children}</div>
    );
  }
}

MarkerReactiveComponent.propTypes = {
  children: React.PropTypes.node,
};
