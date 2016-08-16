import _ from 'lodash';
import { AutoloadPage } from '../../misc/PageLoader';

const KEY_MAP = {
  10: 'enter',
  13: 'enter',
  27: 'esc',
  37: 'left',
  38: 'up',
  39: 'right',
  40: 'down',
  112: 'f1',
  113: 'f2',
  114: 'f3',
  115: 'f4',
  116: 'f5',
  117: 'f6',
  118: 'f7',
  119: 'f8',
  120: 'f9',
  121: 'f10',
  122: 'f11',
  123: 'f12',
};

function isHotkeyMatch(sortedHotkeyArr, hotkeyStr) {
  const hotkeyDefined = hotkeyStr.toLowerCase().split('+');
  return _.isEqual(sortedHotkeyArr, hotkeyDefined.sort());
}

function testElementHotkey(hotkey, $element, attr) {
  if (!$element.is(':visible')) {
    return;
  }
  String($element.attr(attr))
    .split(',')
    .forEach(singleDef => {
      const [defStr, trigger] = singleDef.split(':');
      if (isHotkeyMatch(hotkey, defStr)) {
        switch (trigger) {
        case 'submit':
          $element.closest('form').trigger('submit');
          break;
        case undefined:
          $element.trigger('click');
          break;
        default:
          $element.trigger(trigger);
          break;
        }
      }
    });
}

const hotkeyPage = new AutoloadPage(() => {
  $(document).on('keydown', (ev) => {
    const hotkey = [];
    for (const modifyKey of ['alt', 'ctrl', 'shift']) {
      if (ev[`${modifyKey}Key`]) {
        hotkey.push(modifyKey);
      }
    }
    if (ev.metaKey && !ev.ctrlKey) {
      hotkey.push('ctrl');
    }
    if (KEY_MAP[ev.which] !== undefined) {
      hotkey.push(KEY_MAP[ev.which]);
    } else {
      hotkey.push(String.fromCharCode(ev.which).toLowerCase());
    }
    hotkey.sort();

    // Find all global hotkeys
    for (const element of $('[data-global-hotkey]')) {
      testElementHotkey(hotkey, $(element), 'data-global-hotkey');
    }

    // Find all local hotkeys
    for (const element of $(ev.target).parents('[data-hotkey]')) {
      testElementHotkey(hotkey, $(element), 'data-hotkey');
    }
  });
});

export default hotkeyPage;
