import * as vscode from 'vscode';

interface Finding {
  filePath: string;
  line: number;
  message: string;
  recommendation?: {
    explanation?: string;
    fixedCode?: string;
  };
}

export class FindingItem extends vscode.TreeItem {
  constructor(public readonly finding: Finding, label: string, collapsibleState: vscode.TreeItemCollapsibleState = vscode.TreeItemCollapsibleState.None) {
    super(label, collapsibleState);
    this.command = createOpenFileCommand(finding.filePath, finding.line);
    this.tooltip = createTooltip(finding);
    this.contextValue = finding.recommendation?.fixedCode?.trim() ? 'fixable' : undefined;
  }
}

export class GPTRecommendationItem extends vscode.TreeItem {
  constructor(public readonly finding: Finding) {
    super(`💡 GPT Fix: ${finding.filePath}`, vscode.TreeItemCollapsibleState.None);
    this.command = createOpenFileCommand(finding.filePath, 1);
    this.tooltip = finding.recommendation?.explanation || 'GPT recommendation';
    this.contextValue = 'gptFixable';
  }
}

export class RecommendationProvider implements vscode.TreeDataProvider<vscode.TreeItem>, vscode.Disposable {
  private _onDidChangeTreeData = new vscode.EventEmitter<vscode.TreeItem | undefined | void>();
  readonly onDidChangeTreeData = this._onDidChangeTreeData.event;

  private findings: Finding[] = [];
  private gptRecommendations: Finding[] = [];

  refresh(findings: Finding[], gptRecs: Finding[]) {
    this.findings = findings;
    this.gptRecommendations = gptRecs;
    this._onDidChangeTreeData.fire();
  }

  getTreeItem(element: vscode.TreeItem): vscode.TreeItem {
    return element;
  }

  getChildren(element?: vscode.TreeItem): vscode.ProviderResult<vscode.TreeItem[]> {
    if (!element) {
      return [
        new vscode.TreeItem('Semgrep Findings', vscode.TreeItemCollapsibleState.Collapsed),
        new vscode.TreeItem('GPT Recommendations', vscode.TreeItemCollapsibleState.Collapsed),
      ];
    }

    if (element.label === 'Semgrep Findings') {
      return this.getGroupedFindings();
    }

    if (element.label === 'GPT Recommendations') {
      return this.gptRecommendations.map(finding => new GPTRecommendationItem(finding));
    }

    return this.getFindingsForFile(element.label as string);
  }

  private getGroupedFindings(): vscode.TreeItem[] {
    const grouped = new Map<string, Finding[]>();
    for (const finding of this.findings) {
      if (!grouped.has(finding.filePath)) {
        grouped.set(finding.filePath, []);
      }
      grouped.get(finding.filePath)!.push(finding);
    }

    return Array.from(grouped.keys()).map(file => new vscode.TreeItem(file, vscode.TreeItemCollapsibleState.Collapsed));
  }

  private getFindingsForFile(filePath: string): vscode.TreeItem[] {
    return this.findings
      .filter(f => f.filePath === filePath)
      .map(finding => {
        const label = `🔍 Line ${finding.line}: ${truncateMessage(finding.message)}`;
        return new FindingItem(finding, label);
      });
  }

  dispose() {
    this._onDidChangeTreeData.dispose();
  }
}

// Utility functions
function createOpenFileCommand(filePath: string, line: number): vscode.Command {
  return {
    command: 'vsecure-analyzer.openFileAtLocation',
    title: 'Open File',
    arguments: [filePath, line],
  };
}

function createTooltip(finding: Finding): string {
  return [
    `📄 ${finding.filePath}`,
    `🧠 GPT: ${finding.recommendation?.explanation || ''}`,
    finding.recommendation?.fixedCode ? `💡 Fix:\n${finding.recommendation.fixedCode}` : '',
  ]
    .filter(Boolean)
    .join('\n\n');
}

function truncateMessage(message: string, maxLength: number = 60): string {
  return message.length > maxLength ? `${message.slice(0, maxLength)}...` : message;
}
