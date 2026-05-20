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
