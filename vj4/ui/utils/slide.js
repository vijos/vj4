import delay from './delay';

export async function slideDown($element, duration, fromCss = {}, toCss = {}) {
  const originalStyl = $element.attr('style') || '';
  $element.css({
    position: 'absolute',
    visibility: 'none',
    display: 'block',
  });
  const height = $element.outerHeight();
  $element.attr('style', originalStyl);
  $element.css({
    height: 0,
    overflow: 'hidden',
    display: 'block',
    ...fromCss,
  });
  $element.height();
  $element.transition({
    height,
    ...toCss,
  }, {
    duration,
    easing: 'easeOutCubic',
  });
  await delay(duration);
  $element.attr('style', originalStyl);
  $element.css({
    display: 'block',
  });
}
