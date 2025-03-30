import * as vscode from 'vscode';
import * as fs from 'fs-extra';
import * as path from 'path';
import JSZip from 'jszip';
import axios from 'axios';
import FormData from 'form-data';

export function activate(context: vscode.ExtensionContext) {
  const diagnostics = vscode.languages.createDiagnosticCollection('vsecure-analyzer');
  context.subscriptions.push(diagnostics);

  const runAnalysisCommand = vscode.commands.registerCommand('vsecure-analyzer.runAnalysis', async () => {
    const workspaceFolders = vscode.workspace.workspaceFolders;
    if (!workspaceFolders) {
      vscode.window.showErrorMessage('No folder is open.');
      return;
    }

    const toolChoice = await vscode.window.showQuickPick([
      { label: 'Semgrep only', semgrep: true, codeql: false },
      { label: 'CodeQL only', semgrep: false, codeql: true },
      { label: 'Both Semgrep and CodeQL', semgrep: true, codeql: true }
    ], {
      placeHolder: 'Select which analyzer(s) to run'
    });

    if (!toolChoice) return;

    const rootPath = workspaceFolders[0].uri.fsPath;
    const zip = new JSZip();

    async function addFilesToZip(dir: string, zipFolder: JSZip) {
      const items = await fs.readdir(dir);
      for (const item of items) {
        const fullPath = path.join(dir, item);
        const stat = await fs.stat(fullPath);
        if (stat.isDirectory()) {
          const subFolder = zipFolder.folder(item);
          if (subFolder) await addFilesToZip(fullPath, subFolder);
        } else {
          const fileData = await fs.readFile(fullPath);
          zipFolder.file(item, fileData);
        }
      }
    }

    try {
      vscode.window.showInformationMessage('Compressing and sending to analyzer server...');
      await addFilesToZip(rootPath, zip);
      const zipBlob = await zip.generateAsync({ type: 'nodebuffer' });

      const config = vscode.workspace.getConfiguration("vsecureAnalyzer");
      const serverUrl = config.get<string>("serverUrl") || "http://localhost:8000/analyze";
      const openaiApiKey = config.get<string>("openaiApiKey") || "";

      const formData = new FormData();
      formData.append("code_zip", zipBlob, {
        filename: "code.zip",
        contentType: "application/zip"
      });
      formData.append("run_semgrep_flag", toolChoice.semgrep.toString());
      formData.append("run_codeql_flag", toolChoice.codeql.toString());
      formData.append("openai_api_key", openaiApiKey);

      const response = await axios.post(serverUrl, formData, {
        headers: formData.getHeaders()
      });

      vscode.window.showInformationMessage('Analysis complete.');
      const semgrepResults = response.data.results?.semgrep || [];
      const codeqlResults = response.data.results?.codeql || [];

      const findings = [...semgrepResults, ...codeqlResults];
      const fileMap: Map<string, vscode.Diagnostic[]> = new Map();

      for (const item of findings) {
        const relPath = item.filePath;
        if (!relPath) continue;

        const fullPath = path.join(rootPath, relPath);
        const range = new vscode.Range(
          new vscode.Position((item.line || 1) - 1, 0),
          new vscode.Position((item.line || 1) - 1, 1000)
        );

        const source = item.tool || 'vsecure-analyzer';

        let message = `🔍 [${source}] ${item.message}`;
        if (item.recommendation?.explanation) {
          message += `\n💡 GPT: ${item.recommendation.explanation}`;
        }

        const diagnostic = new vscode.Diagnostic(
          range,
          message,
          vscode.DiagnosticSeverity.Warning
        );
        diagnostic.source = source;

        const uri = vscode.Uri.file(fullPath);
        if (!fileMap.has(uri.fsPath)) {
          fileMap.set(uri.fsPath, []);
        }
        fileMap.get(uri.fsPath)?.push(diagnostic);
      }

      diagnostics.clear();
      for (const [file, diags] of fileMap.entries()) {
        const uri = vscode.Uri.file(file);
        diagnostics.set(uri, diags);
      }
    } catch (err: any) {
      vscode.window.showErrorMessage('Analysis failed: ' + err.message);
    }
  });

  const gptFixCommand = vscode.commands.registerCommand('vsecure-analyzer.requestGptFix', async () => {
    const editor = vscode.window.activeTextEditor;
    if (!editor) return;

    const selection = editor.selection;
    const selectedText = editor.document.getText(selection);
    const config = vscode.workspace.getConfiguration("vsecureAnalyzer");
    const serverUrl = config.get<string>("serverUrl") || "http://localhost:8000/fix";
    const openaiApiKey = config.get<string>("openaiApiKey") || "";

    const formData = new FormData();
    formData.append("message", "Fix this vulnerable code.");
    formData.append("code", selectedText);
    formData.append("openai_api_key", openaiApiKey);

    try {
      vscode.window.showInformationMessage("Requesting GPT fix...");
      const response = await axios.post(serverUrl, formData, {
        headers: formData.getHeaders()
      });

      const fixedCode = response.data.fixedCode;
      if (!fixedCode) {
        vscode.window.showWarningMessage("GPT returned no fix.");
        return;
      }

      const panel = vscode.window.createWebviewPanel(
        'gptFixPreview',
        'GPT Suggested Fix',
        vscode.ViewColumn.Beside,
        { enableScripts: true }
      );

      panel.webview.html = `
        <html>
          <head>
            <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline';">
            <style>
              body {
                font-family: var(--vscode-font-family, sans-serif);
                background-color: var(--vscode-editor-background);
                color: var(--vscode-editor-foreground);
                padding: 16px;
              }
              .code-block {
                background-color: var(--vscode-editor-background);
                color: var(--vscode-editor-foreground);
                padding: 12px;
                border-radius: 6px;
                white-space: pre-wrap;
                font-family: var(--vscode-editor-font-family, monospace);
                border: 1px solid var(--vscode-editorWidget-border);
              }
              button {
                margin-top: 20px;
                padding: 8px 16px;
                background-color: var(--vscode-button-background);
                color: var(--vscode-button-foreground);
                border: none;
                border-radius: 4px;
                cursor: pointer;
              }
              button:hover {
                background-color: var(--vscode-button-hoverBackground);
              }
            </style>
          </head>
          <body>
            <h2>💡 GPT Suggested Fix</h2>
            <h4>Original Code</h4>
            <div class="code-block">${selectedText.replace(/</g, "&lt;")}</div>
            <h4>Fixed Code</h4>
            <div class="code-block">${fixedCode.replace(/</g, "&lt;")}</div>
            <button onclick="vscode.postMessage({ apply: true })">Apply Fix</button>
            <script>
              const vscode = acquireVsCodeApi();
            </script>
          </body>
        </html>
      `;

      panel.webview.onDidReceiveMessage(message => {
        if (message.apply) {
          editor.edit(editBuilder => {
            editBuilder.replace(selection, fixedCode);
          });
          vscode.window.showInformationMessage("GPT fix applied.");
          panel.dispose();
        }
      });

    } catch (err: any) {
      vscode.window.showErrorMessage("GPT fix failed: " + err.message);
    }
  });

  context.subscriptions.push(runAnalysisCommand);
  context.subscriptions.push(gptFixCommand);
}

export function deactivate() {}
