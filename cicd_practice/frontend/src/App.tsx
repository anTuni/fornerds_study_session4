import { FilePlus2, LayoutDashboard, LogIn, Search, ShieldCheck, UserCog } from 'lucide-react';
import { FormEvent, useMemo, useState } from 'react';
import { ApiClient, ContentItem, ContentStatus, CurrentUser } from './api';

export function App() {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('token'));
  const [user, setUser] = useState<CurrentUser | null>(() => {
    const raw = localStorage.getItem('user');
    return raw ? JSON.parse(raw) as CurrentUser : null;
  });
  const [contents, setContents] = useState<ContentItem[]>([]);
  const [query, setQuery] = useState('');
  const [message, setMessage] = useState('로그인 후 콘텐츠를 관리하세요.');
  const api = useMemo(() => new ApiClient(token), [token]);

  async function login(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const result = await api.login(String(form.get('email')), String(form.get('password')));
    setToken(result.token);
    setUser(result.user);
    localStorage.setItem('token', result.token);
    localStorage.setItem('user', JSON.stringify(result.user));
    setMessage(`${result.user.displayName}님으로 로그인했습니다.`);
  }

  async function loadContents(event?: FormEvent) {
    event?.preventDefault();
    const result = await api.listContents(query);
    setContents(result);
    setMessage(`${result.length}개의 콘텐츠를 불러왔습니다.`);
  }

  async function createContent(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    await api.createContent({
      title: String(form.get('title')),
      body: String(form.get('body')),
      status: String(form.get('status')) as ContentStatus,
    });
    event.currentTarget.reset();
    await loadContents();
  }

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <ShieldCheck size={28} />
          <div>
            <strong>CICD Practice</strong>
            <span>Security CMS</span>
          </div>
        </div>
        <nav>
          <button title="대시보드"><LayoutDashboard size={18} />대시보드</button>
          <button title="회원 관리"><UserCog size={18} />회원 관리</button>
          <button title="콘텐츠 작성"><FilePlus2 size={18} />콘텐츠</button>
        </nav>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div>
            <h1>콘텐츠 관리</h1>
            <p>{message}</p>
          </div>
          {user && <span className="role-badge">{user.role}</span>}
        </header>

        <section className="panel auth-panel">
          <form onSubmit={login}>
            <input name="email" type="email" defaultValue="admin@example.com" aria-label="email" />
            <input name="password" type="password" defaultValue="admin1234" aria-label="password" />
            <button type="submit"><LogIn size={18} />로그인</button>
          </form>
        </section>

        <section className="content-grid">
          <div className="panel">
            <div className="panel-heading">
              <h2>콘텐츠 목록</h2>
              <form className="search-form" onSubmit={loadContents}>
                <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="검색어" />
                <button type="submit" title="검색"><Search size={18} /></button>
              </form>
            </div>
            <div className="list">
              {contents.map((content) => (
                <article className="content-card" key={content.id}>
                  <div>
                    <strong>{content.title}</strong>
                    <span>{content.status} · {content.authorName}</span>
                  </div>
                  <p>{content.body}</p>
                </article>
              ))}
            </div>
          </div>

          <form className="panel editor" onSubmit={createContent}>
            <h2>새 콘텐츠</h2>
            <input name="title" placeholder="제목" required />
            <textarea name="body" placeholder="본문" required />
            <select name="status" defaultValue="DRAFT">
              <option value="DRAFT">초안</option>
              <option value="PUBLISHED">게시</option>
              <option value="ARCHIVED">보관</option>
            </select>
            <button type="submit"><FilePlus2 size={18} />저장</button>
          </form>
        </section>
      </section>
    </main>
  );
}
