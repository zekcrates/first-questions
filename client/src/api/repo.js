import { apiFetch } from './client.js';

/**
 * Index a repo (clone + local embed → .pkl). Uses server file cache — second call is instant.
 * @param {{ repoUrl: string, language?: string, accessToken?: string, signal?: AbortSignal }} opts
 * @returns {Promise<{status: string, repo_name: string, cached: boolean, message: string}>}
 */
export function prepareRepo({ repoUrl, language = 'en', accessToken, signal } = {}) {
  if (!repoUrl) throw new Error('repoUrl is required');
  return apiFetch('/api/prepare', {
    method: 'POST',
    body: { repo_url: repoUrl, language, access_token: accessToken },
    signal,
  });
}

/**
 * Get 30-40 hypotheses for a repo. File-cache hit returns instantly, no LLM call.
 * @param {{ repoUrl: string, language?: string, provider?: string, model?: string, force?: boolean, accessToken?: string, signal?: AbortSignal }} opts
 * @returns {Promise<{questions: Array<{id:number,question:string,target_files:string[],target_functions:string[]}>, cached: boolean, repo_name: string}>}
 */
export function fetchQuestions({ repoUrl, language = 'en', provider, model, force = false, accessToken, signal } = {}) {
  if (!repoUrl) throw new Error('repoUrl is required');
  return apiFetch('/api/questions', {
    method: 'POST',
    body: {
      repo_url: repoUrl,
      language,
      provider,
      model,
      force,
      access_token: accessToken,
    },
    signal,
  });
}
