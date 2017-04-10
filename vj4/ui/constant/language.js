import attachObjectMeta from './util/objectMeta';

export const LANG_TEXTS = {
  c: 'C',
  cc: 'C++',
  pas: 'Pascal',
  java: 'Java',
  py: 'Python',
  php: 'PHP',
};

export const LANG_CODEMIRROR_MODES = {
  c: 'text/x-csrc',
  cc: 'text/x-c++src',
  pas: 'text/x-pascal',
  java: 'text/x-java',
  py: 'text/x-python',
  php: 'text/x-php',
};
attachObjectMeta(LANG_CODEMIRROR_MODES, 'exportToPython', false);
