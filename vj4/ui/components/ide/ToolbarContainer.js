import React from 'react';
import { connect } from 'react-redux';
import Toolbar from './ToolbarComponent';

const ToolbarContainer = (props) => (
  <Toolbar
    extra={
      <span></span>
    }
  >
    abc
  </Toolbar>
);

const mapStateToProps = (state) => ({
});

const mapDispatchToProps = (dispatch) => ({
});

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(ToolbarContainer);

