import * as React from "react";
import { MonacoEditorProps } from "./types";
import { noop } from "./utils";
declare function MonacoEditor({ width, height, value, defaultValue, language, theme, options, overrideServices, editorWillMount, editorDidMount, editorWillUnmount, onChange, className, uri, }: MonacoEditorProps): React.JSX.Element;
declare namespace MonacoEditor {
    var defaultProps: {
        width: string;
        height: string;
        value: any;
        defaultValue: string;
        language: string;
        theme: any;
        options: {};
        overrideServices: {};
        editorWillMount: typeof noop;
        editorDidMount: typeof noop;
        editorWillUnmount: typeof noop;
        onChange: typeof noop;
        className: any;
    };
    var displayName: string;
}
export default MonacoEditor;
