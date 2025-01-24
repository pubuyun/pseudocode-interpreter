import React from "react";
import { createRoot } from "react-dom/client";
import MonacoEditor from "react-monaco-editor";
import data from './autocomplete.json';
import "./styles.css"; 
import OneDarkPro from "./themes/OneDark-Pro.json";
import GithubLight from "./themes/GitHub Light.json";

class CodeEditor extends React.Component {
  constructor() {
    super();
    
    this.state = {
      code: "OUTPUT \"HelloWorld\"",
      theme: "one-dark-pro",
      output: "",
      inputText: "", // 新增状态用于存储输入框内容
      socket: null,
      reconnectAttempts: 0, 
      isError: false 
    };
    this.variables = new Set();
    
  }
  connectWebSocket = () => {
    const socket = new WebSocket("ws://120.25.192.109:5000/");
  
    socket.onopen = () => {
      console.log("WebSocket connected");
      this.setState({ socket, reconnectAttempts: 0 });
    };
  
    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      // 检查消息中是否包含 error 字段
      if (data.error) {
        this.setState((prevState) => ({
          output: prevState.output + data.error,
          isError: true // 标记为错误信息
        }));
      } else {
        this.setState((prevState) => ({
          output: prevState.output + data.output,
          isError: false // 普通信息
        }));
      }
    };
  
    socket.onclose = () => {
      console.log("WebSocket closed, attempting to reconnect...");
      this.setState({ socket: null });
      this.reconnect();
    };
  
    this.setState({ socket });
  };
  
  componentDidMount() {
    const savedCode = localStorage.getItem("savedCode");
    if (savedCode) {
      this.setState({ code: savedCode });
    }
    this.connectWebSocket();
  }

  reconnect = () => {
    const { reconnectAttempts } = this.state;

    if (reconnectAttempts < 10) { // 限制最大重连次数
      setTimeout(() => {
        console.log(`Reconnection attempt #${reconnectAttempts + 1}`);
        this.setState({ reconnectAttempts: reconnectAttempts + 1 });
        this.connectWebSocket();
      }, 2000); // 设置重连间隔时间，单位为毫秒
    } else {
      console.log("Maximum reconnection attempts reached.");
    }
  };

  componentWillUnmount() {
    if (this.state.socket) {
      this.state.socket.close();
    }
  }
  sendInputToSocket = () => {
    const { socket, inputText } = this.state;
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({ input: inputText }));
      console.log("Input sent");
      this.setState({inputText: ""})
    }
  };

  editorWillMount = (monaco) => {
    console.log(OneDarkPro);
    console.log(GithubLight);
    monaco.editor.defineTheme("one-dark-pro", OneDarkPro);
    monaco.editor.defineTheme("github-light", GithubLight);

    const kindMapping = {
      Keyword: monaco.languages.CompletionItemKind.Keyword,
      Function: monaco.languages.CompletionItemKind.Function,
      Variable: monaco.languages.CompletionItemKind.Variable,
    };
    // 注册自定义语言
    monaco.languages.register({ id: "PseudoCode" });

    monaco.languages.setMonarchTokensProvider("PseudoCode", {
      tokenizer: {
        root: [
          // 忽略的内容，如注释和空格
          [/\/*.*\*\//, "comment"],          // 多行注释
          [/\/\/.*$/, "comment"],            // 单行注释
          [/[ \t]+/, "white"],               // 空格
          
          // 关键字
          [/\b(PROCEDURE|ENDPROCEDURE|FUNCTION|RETURNS|ENDFUNCTION|IF|THEN|ELSE|ENDIF|CASE OF|OF|OTHERWISE|ENDCASE|FOR|TO|STEP|NEXT|REPEAT|UNTIL|WHILE|DO|ENDWHILE|DECLARE|CONSTANT|INPUT|OUTPUT|RETURN|OPENFILE|READFILE|WRITEFILE|CLOSEFILE|CALL|ARRAY|INTEGER|REAL|CHAR|STRING|BOOLEAN|READ|WRITE|TRUE|FALSE|AND|OR|NOT)\b/, "keyword"],
    
          // 符号
          [/[()]/, "@brackets"],               // 括号
          [/\[|\]/, "@brackets"],               // 方括号
          [/\,/, "delimiter"],                  // 逗号
          [/(:|<-|=|<=|>=|<>|<|>|\+|&|-|\*|\/|\^|DIV|MOD)/, "operator"],
    
          // 字面量：数字和字符串
          [/-?[0-9]+(?:\.[0-9]+)?/, "number"],  // 数字
          [/".*?"/, "string"],                  // 字符串
    
          // 标识符（变量名或函数名）
          [/[A-Za-z_][A-Za-z0-9_]*/, "identifier"],
    
          // 其它
          [/./, "invalid"],                     // 未知字符
        ],
      },
    
      // 定义注释样式和配对符号
      comments: {
        lineComment: "//",
        blockComment: ["/*", "*/"]
      }  
    });    

    monaco.languages.setLanguageConfiguration('PseudoCode', {autoClosingPairs: [
      { open: "(", close: ")", notIn: ["string", "comment"] },
      { open: "[", close: "]", notIn: ["string", "comment"] },
      { open: "{", close: "}", notIn: ["string", "comment"] },
      { open: '"', close: '"', notIn: ["string"] },
      { open: '/*', close: '*/', notIn: ["string"] }
    ]} );
    monaco.languages.registerCompletionItemProvider("PseudoCode", {
      provideCompletionItems: (model, position) => {
        // 获取当前文本内容
        const code = model.getValue();
        this.variables.clear();
          // 提取 DECLARE 声明的变量名
          const declareRegex = /\bDECLARE\b\s+([A-Za-z_][A-Za-z0-9_]*(?:\s*,\s*[A-Za-z_][A-Za-z0-9_]*)*):/g;
          let match;
          while ((match = declareRegex.exec(code)) !== null) {
            const variableName = match[1];
            this.variables.add(variableName);
          }

        // 提取 FOR 循环中定义的变量名
        const forLoopRegex = /\bFOR\b\s+([A-Za-z_][A-Za-z0-9_]*)\s*<-/g;
        while ((match = forLoopRegex.exec(code)) !== null) {
          const variableName = match[1];
          this.variables.add(variableName);
        }

        // 将变量名添加到补全项
        const variableSuggestions = Array.from(this.variables).map((variable) => ({
          label: variable,
          kind: monaco.languages.CompletionItemKind.Variable,
          insertText: variable,
          documentation: "User-defined variable",
        }));

        return {suggestions:[
          ...variableSuggestions,
          ...data.map(item => ({
            label: item.label,
            kind: kindMapping[item.kind] || monaco.languages.CompletionItemKind.Text, // 默认值
            insertText: item.insertText,
            documentation: item.documentation,
          }))
        ]};
      }
  })
  }
  onChange = (newValue) => {
    this.setState({ code: newValue });
    localStorage.setItem("savedCode", newValue); // 保存代码到 localStorage
  };

  toggleTheme = () => {
    const newTheme = this.state.theme === 'github-light' ? 'one-dark-pro' : 'github-light';
    this.setState({ theme: newTheme });
  };

  editorDidMount = (editor) => {
    this.editor = editor;
  };

  changeEditorValue = () => {
    if (this.editor) {
      this.editor.setValue("// code changed! \n");
    }
  };

  changeBySetState = () => {
    this.setState({ code: "// code changed by setState! \n" });
  };

  setDarkTheme = () => {
    this.setState({ theme: "one-dark-pro" });
  };

  setLightTheme = () => {
    this.setState({ theme: "github-light" });
  };

  runCode = () => {
    const { socket, code } = this.state;
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({ code }));
      this.setState({ output: "", isError: false });
    }
  };

  handleInputChange = (newValue) => {
    this.setState({ inputText: newValue });
  };

  render() {
    const { code, theme, output, inputText, isError } = this.state;
    document.documentElement.style.setProperty("--bg-color", theme === "one-dark-pro" ? "#282c36" : "#fbfbfb");
    document.documentElement.style.setProperty("--text-color", theme === "one-dark-pro" ? "#ffffff" : "#222222");
    document.documentElement.style.setProperty("--heading-color", theme === "one-dark-pro" ? "#ffffff" : "#333333");

    return (
      <div className="container custom">
        <div className="sidebar custom">
          <button onClick={this.runCode}>Run Code</button>
          <button onClick={this.toggleTheme}>
            {theme === "github-light" ? "Switch to Dark" : "Switch to Light"}
          </button>
          <h3>Input</h3>
          <MonacoEditor
            height="200"
            language="plaintext"
            value={inputText}
            onChange={this.handleInputChange}
            theme={theme}
          />
          <button onClick={this.sendInputToSocket}>Send</button>
          <h3>Output</h3>
          <MonacoEditor
            height="200"
            language="plaintext"
            value={output}
            options={{ readOnly: true }}
            theme={theme}
            className={isError ? "output-error" : ""}
          />
        </div>
        <div className="main-editor">
          <MonacoEditor
            height="100vh"
            width="100%"
            language="PseudoCode"
            value={code}
            onChange={this.onChange}
            theme={theme}
            editorWillMount={this.editorWillMount}
          />
        </div>
      </div>
    );
  }
}

const App = () => (
  <div>
    <h2>Pseudo Editor</h2>
    <CodeEditor />
    <hr />
  </div>
);

const container = document.getElementById("root");

const loadingContainer = document.getElementById("loading-container");
if (loadingContainer) {
    loadingContainer.remove();
}

const root = createRoot(container);
root.render(<App />);
