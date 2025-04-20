import axios from 'axios';
import FormData from 'form-data';

export interface AnalysisResult {
  semgrep?: any[];
  codeql?: any[];
}

export async function analyzeCode(
  zipBlob: Buffer,
  serverUrl: string,
  toolChoice: { semgrep: boolean; codeql: boolean },
  openaiApiKey: string
): Promise<AnalysisResult> {
  const formData = new FormData();
  formData.append('code_zip', zipBlob, { filename: 'code.zip', contentType: 'application/zip' });
  formData.append('run_semgrep_flag', String(toolChoice.semgrep));
  formData.append('run_codeql_flag', String(toolChoice.codeql));
  formData.append('openai_api_key', openaiApiKey);

  const response = await axios.post(serverUrl, formData, { headers: formData.getHeaders() });
  return response.data.results;
}