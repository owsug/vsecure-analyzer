import * as vscode from 'vscode';
import * as path from 'path';
import { createZipFromDirectory } from './utils/zipUtils';
import * as fs from 'fs/promises';
import { analyzeCode } from './api/analyze';
import { applyFix } from './api/fix';
import { RecommendationProvider } from './tree/RecommendationProvider';

export function activate(context: vscode.ExtensionContext) {
  const treeProvider = new RecommendationProvider();
  vscode.window.createTreeView('vsecure-analyzer-view', { treeDataProvider: treeProvider });
  context.subscriptions.push(treeProvider);

  const statusBar = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left);
  context.subscriptions.push(statusBar);

  const runAnalysis = vscode.commands.registerCommand('vsecure-analyzer.runAnalysis', async () => {
    const workspaceFolders = vscode.workspace.workspaceFolders;
    if (!workspaceFolders) {
      vscode.window.showErrorMessage('No folder is open.');
      return;
    }
    statusBar.text = 'Analyzing...';
    statusBar.show();

    const rootPath = workspaceFolders[0].uri.fsPath;

    try {
      // Create zip from the root directory
      const zipBlob = await createZipFromDirectory(rootPath);

      const config = vscode.workspace.getConfiguration("vsecureAnalyzer");
      const serverUrl = config.get<string>("serverUrl") || "http://localhost:8000/analyze";
      const openaiApiKey = config.get<string>("openaiApiKey") || "";

      const toolChoice = await vscode.window.showQuickPick([
        { label: 'Semgrep only', semgrep: true, codeql: false },
        { label: 'CodeQL only', semgrep: false, codeql: true },
        { label: 'Both', semgrep: true, codeql: true }
      ], { placeHolder: 'Which analysis tools to use?' });

      if (!toolChoice) { return; }

      vscode.window.showInformationMessage('Analyzing source code...');
      const resultData = await analyzeCode(zipBlob, serverUrl, toolChoice, openaiApiKey);

      const rootUri = vscode.workspace.workspaceFolders?.[0].uri.fsPath || "";
      const allFindings = [
        ...(resultData.semgrep || []),
        ...(resultData.codeql || [])
      ];

      const gptRecs: any[] = [];
      for (const finding of allFindings) {
        const line = finding.line || 1;
        const fullPath = path.join(rootUri, finding.filePath);
        try {
          const lines = await fs.readFile(fullPath, 'utf8');
          const lineText = lines.split('\n')[line - 1] || '';
          finding.code = lineText;
        } catch {
          finding.code = '';
        }

        if (!finding.recommendation) { finding.recommendation = {}; }

        if (finding.recommendation.fixedCode) {
          const exists = gptRecs.find(item => item.filePath === finding.filePath);
          if (!exists) { gptRecs.push(finding); }
        }
      }

      treeProvider.refresh(allFindings, gptRecs);
      statusBar.text = 'Analysis completed';
      setTimeout(() => { statusBar.hide(); }, 5000);
    } catch (err: any) {
      vscode.window.showErrorMessage('Analysis failed: ' + err.message);
      statusBar.text = 'Analysis failed';
      setTimeout(() => { statusBar.hide(); }, 5000);
    }
  });

  const applyFixCommand = vscode.commands.registerCommand('vsecure-analyzer.applyFixCommand', async (item: any) => {
    const finding = item?.finding;
    if (!finding || !finding.filePath) {
      vscode.window.showErrorMessage("Invalid fix target.");
      return;
    }

    const isGpt = item.contextValue === 'gptFixable';
    const workspaceRoot = vscode.workspace.workspaceFolders?.[0].uri.fsPath || "";

    await applyFix(finding, isGpt, workspaceRoot);

    vscode.window.showInformationMessage("Fix applied. Run analysis again?", "Yes").then(sel => {
      if (sel === "Yes")  {
        vscode.commands.executeCommand("vsecure-analyzer.runAnalysis");
      }
    });
  });

  context.subscriptions.push(runAnalysis, applyFixCommand);
}

export function deactivate() {}