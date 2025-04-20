import * as vscode from 'vscode';
import * as path from 'path';

export async function applyFix(
  finding: any,
  isGpt: boolean,
  workspaceRoot: string
): Promise<void> {
  const fileUri = vscode.Uri.file(path.join(workspaceRoot, finding.filePath));
  const doc = await vscode.workspace.openTextDocument(fileUri);

  const fixedCode = finding.recommendation?.fixedCode?.trim();
  if (!fixedCode) {
    vscode.window.showErrorMessage("No fix available.");
    return;
  }

  const confirmMsg = isGpt
    ? "This fix will replace the entire file and may invalidate other findings. Continue?"
    : "Apply fix for this line?";

  const accept = await vscode.window.showInformationMessage(confirmMsg, "Yes", "Cancel");
  if (accept !== "Yes") { return; }

  const edit = new vscode.WorkspaceEdit();
  if (isGpt) {
    edit.replace(fileUri, new vscode.Range(0, 0, doc.lineCount, 0), fixedCode + "\n");
  } else {
    const startLine = Math.max(0, finding.line - 1);
    edit.replace(fileUri, new vscode.Range(startLine, 0, startLine + 1, 0), fixedCode + "\n");
  }
  await vscode.workspace.applyEdit(edit);
}