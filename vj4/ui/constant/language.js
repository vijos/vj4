import attachObjectMeta from './util/objectMeta';

export const LANG_TEXTS = {
  c: 'C',
  cc: 'C++',
  pas: 'Pascal',
  java: 'Java',
  py: 'Python',
};

export const LANG_CODEMIRROR_MODES = {
  c: 'text/x-csrc',
  cc: 'text/x-c++src',
  pas: 'text/x-pascal',
  java: 'text/x-java',
  py: 'text/x-python',
};
attachObjectMeta(LANG_CODEMIRROR_MODES, 'exportToPython', false);
