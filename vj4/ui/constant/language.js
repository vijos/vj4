import attachObjectMeta from './util/objectMeta';

export const LANG_TEXTS = {
  c: 'C',
  cc: 'C++',
  pas: 'Pascal',
  java: 'Java',
  py: 'Python',
  py3: 'Python 3',
  php: 'PHP',
  rs: 'Rust',
  hs: 'Haskell',
};

export const LANG_HIGHLIGHT_ID = {
  c: 'c',
  cc: 'cpp',
  pas: 'pascal',
  java: 'java',
  py: 'python',
  py3: 'python',
  php: 'php',
  rs: 'rust',
  hs: 'haskell',
};

export const LANG_CODEMIRROR_MODES = {
  c: 'text/x-csrc',
  cc: 'text/x-c++src',
  pas: 'text/x-pascal',
  java: 'text/x-java',
  py: 'text/x-python',
  py3: 'text/x-python',
  php: 'text/x-php',
  rs: 'text/x-rustsrc',
  hs: 'text/x-haskell',
};
attachObjectMeta(LANG_CODEMIRROR_MODES, 'exportToPython', false);
