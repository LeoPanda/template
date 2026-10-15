/**
 * ローカル Sidecar API 通信用クライアント
 * (X-App-Session-Token を自動注入し、マシン内境界を保護)
 */

interface RequestOptions extends RequestInit {
  params?: Record<string, string | number>;
}

class ApiClient {
  private baseUrl: string = 'http://127.0.0.1:54321';
  private sessionToken: string = '';

  public setConfig(port: number, token: string) {
    this.baseUrl = `http://127.0.0.1:${port}`;
    this.sessionToken = token;
  }

  async request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
    const url = new URL(`${this.baseUrl}${endpoint}`);
    if (options.params) {
      Object.entries(options.params).forEach(([k, v]) =>
        url.searchParams.append(k, String(v))
      );
    }

    const headers = new Headers(options.headers || {});
    headers.set('Content-Type', 'application/json');
    if (this.sessionToken) {
      headers.set('X-App-Session-Token', this.sessionToken);
    }

    const response = await fetch(url.toString(), {
      ...options,
      headers,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`API Error [${response.status}]: ${errorText}`);
    }

    return response.json() as Promise<T>;
  }

  get<T>(endpoint: string, options?: RequestOptions) {
    return this.request<T>(endpoint, { ...options, method: 'GET' });
  }

  post<T>(endpoint: string, body?: unknown, options?: RequestOptions) {
    return this.request<T>(endpoint, {
      ...options,
      method: 'POST',
      body: body ? JSON.stringify(body) : undefined,
    });
  }
}

export const apiClient = new ApiClient();
