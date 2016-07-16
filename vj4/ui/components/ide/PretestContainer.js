import React from 'react';
import { connect } from 'react-redux';
import Pane from './PaneComponent';

const PretestContainer = (props) => (
  <Pane>Pretest</Pane>
);

const mapStateToProps = (state) => ({
});

const mapDispatchToProps = (dispatch) => ({
});

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(PretestContainer);
