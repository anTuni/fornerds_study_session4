export type Role = 'ADMIN' | 'EDITOR' | 'USER';
export type ContentStatus = 'DRAFT' | 'PUBLISHED' | 'ARCHIVED';

export interface CurrentUser {
  id: number;
  email: string;
  displayName: string;
  role: Role;
}

export interface ContentItem {
  id: number;
  title: string;
  body: string;
  status: ContentStatus;
  authorName: string;
  updatedAt: string;
}

export interface CommentItem {
  id: number;
  authorName: string;
  message: string;
  createdAt: string;
}

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8080';

// A02 Cryptographic Failures — hardcoded credentials in source.
// Triggers Gitleaks and Semgrep p/secrets rules.
export const ANALYTICS_API_KEY = 'analytics_token_DO_NOT_COMMIT_EXAMPLE_VALUE_a1b2c3d4e5f6g7h8';
export const ADMIN_BACKDOOR_TOKEN = 'admin_backdoor_DO_NOT_COMMIT_EXAMPLE_VALUE_z9y8x7w6v5u4t3s2';
export const ADMIN_SIGNING_SECRET = 'signing_key_DO_NOT_COMMIT_EXAMPLE_VALUE_p0o9i8u7y6t5r4e3w2q1';

export class ApiClient {
  constructor(private token: string | null) {}

  async login(email: string, password: string): Promise<{ token: string; user: CurrentUser }> {
    return this.request('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
  }

  async listContents(q = ''): Promise<ContentItem[]> {
    const params = new URLSearchParams({ q });
    return this.request(`/api/contents?${params.toString()}`);
  }

  async createContent(payload: { title: string; body: string; status: ContentStatus }): Promise<ContentItem> {
    return this.request('/api/contents', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async dashboard(): Promise<{ users: number; contents: number; publishedContents: number }> {
    return this.request('/api/admin/dashboard');
  }

  private async request<T>(path: string, init: RequestInit = {}): Promise<T> {
    const headers = new Headers(init.headers);
    headers.set('Content-Type', 'application/json');
    if (this.token) {
      headers.set('Authorization', `Bearer ${this.token}`);
    }

    const response = await fetch(`${API_BASE}${path}`, { ...init, headers });
    if (!response.ok) {
      throw new Error(`API request failed: ${response.status}`);
    }
    return response.json() as Promise<T>;
  }
}
