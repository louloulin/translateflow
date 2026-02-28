import React, { useRef, useEffect } from 'react';
import Editor, { OnMount, OnChange } from '@monaco-editor/react';
import type { editor } from 'monaco-editor';

interface MonacoEditorProps {
  value: string;
  onChange?: (value: string) => void;
  language?: string;
  readOnly?: boolean;
  height?: string | number;
  theme?: 'vs-dark' | 'light' | 'hc-black';
  options?: editor.IStandaloneEditorConstructionOptions;
  onEditorMount?: (editor: editor.IStandaloneCodeEditor) => void;
  autoFocus?: boolean;
}

export const MonacoEditor: React.FC<MonacoEditorProps> = ({
  value,
  onChange,
  language = 'plaintext',
  readOnly = false,
  height = '100%',
  theme = 'vs-dark',
  options = {},
  onEditorMount,
  autoFocus = false
}) => {
  const editorRef = useRef<editor.IStandaloneCodeEditor | null>(null);

  const handleEditorDidMount: OnMount = (editor, monaco) => {
    editorRef.current = editor;

    // Configure editor settings
    editor.updateOptions({
      minimap: { enabled: false },
      scrollBeyondLastLine: false,
      lineNumbers: 'on',
      glyphMargin: false,
      folding: false,
      lineDecorationsWidth: 10,
      lineNumbersMinChars: 3,
      renderLineHighlight: 'line',
      scrollbar: {
        vertical: 'auto',
        horizontal: 'auto',
        verticalScrollbarSize: 10,
        horizontalScrollbarSize: 10
      },
      overviewRulerLanes: 0,
      hideCursorInOverviewRuler: true,
      overviewRulerBorder: false,
      wordWrap: 'on',
      automaticLayout: true,
      fontSize: 13,
      fontFamily: "'SF Mono', 'Fira Code', 'Consolas', monospace",
      fontLigatures: true,
      ...options
    });

    // Auto-focus if requested
    if (autoFocus) {
      editor.focus();
    }

    // Callback for parent component
    if (onEditorMount) {
      onEditorMount(editor);
    }
  };

  const handleChange: OnChange = (value, event) => {
    if (onChange && value !== undefined) {
      onChange(value);
    }
  };

  return (
    <Editor
      height={height}
      language={language}
      value={value}
      onChange={handleChange}
      onMount={handleEditorDidMount}
      theme={theme}
      options={{
        readOnly,
        ...options
      }}
    />
  );
};

// Lightweight inline editor for single-line or short text
export const MonacoInlineEditor: React.FC<Omit<MonacoEditorProps, 'height'>> = ({
  value,
  onChange,
  ...props
}) => {
  return (
    <MonacoEditor
      value={value}
      onChange={onChange}
      height={80}
      options={{
        minimap: { enabled: false },
        lineNumbers: 'off',
        glyphMargin: false,
        folding: false,
        lineDecorationsWidth: 0,
        lineNumbersMinChars: 0,
        renderLineHighlight: 'none',
        scrollbar: {
          vertical: 'hidden',
          horizontal: 'hidden'
        },
        overviewRulerLanes: 0,
        wordWrap: 'on',
        automaticLayout: true,
        fontSize: 13,
        ...props.options
      }}
      {...props}
    />
  );
};
