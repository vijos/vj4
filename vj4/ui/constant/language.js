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

export const LANG_CLASSES = {
  c: 'language-c',
  cc: 'language-cpp',
  pas: 'language-pascal',
  java: 'language-java',
  py: 'language-python',
  py3: 'language-python',
  php: 'language-php',
  rs: 'language-rust',
  hs: 'language-haskell',
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
