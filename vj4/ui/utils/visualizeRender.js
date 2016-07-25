import visualizeRenderDecorator from 'react-render-visualizer-decorator';

const ENABLED = true;

export default function visualizeRender(...argv) {
  if (ENABLED) {
    return visualizeRenderDecorator(...argv);
  } else {
    return argv[0];
  }
}
