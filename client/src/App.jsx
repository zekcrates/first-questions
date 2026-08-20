import { useRef, useState } from 'react'

const languages = ['Python', 'TypeScript', 'JavaScript', 'Rust', 'Go', 'Java', 'C++', 'Ruby']
const owners = ['zekcrates', 'tw93', 'sindresorhus', 'tj', 'indutny', 'codelibs']

const repos = [
  { owner: 'microsoft', name: 'vscode', desc: 'Visual Studio Code', stars: '188.6k', language: 'TypeScript', updated: 'Mar 1, 2026' },
  { owner: 'huggingface', name: 'transformers', desc: '🤗 Transformers: the model-definition framework for state-of-the-art machine learning models in text, vision, audio, and multimodal models, for both inference and training.', stars: '164.0k', language: 'Python', updated: 'Mar 2, 2026' },
  { owner: 'langchain-ai', name: 'langchain', desc: 'The agent engineering platform.', stars: '144.1k', language: 'Python', updated: 'Feb 28, 2026' },
  { owner: 'microsoft', name: 'playwright', desc: 'Playwright is a framework for Web Testing and Automation. It allows testing Chromium, Firefox and WebKit with a single API.', stars: '94.4k', language: 'TypeScript', updated: 'Mar 1, 2026' },
  { owner: 'mermaid-js', name: 'mermaid', desc: 'Generation of diagrams like flowcharts or sequence diagrams from text in a similar manner as markdown', stars: '89.7k', language: 'JavaScript', updated: 'Feb 27, 2026' },
  { owner: 'opendatalab', name: 'MinerU', desc: 'Transforms complex documents like PDFs and Office docs into LLM-ready markdown/JSON for your Agentic workflows.', stars: '77.4k', language: 'Python', updated: 'Mar 2, 2026' },
  { owner: 'karpathy', name: 'nanochat', desc: 'The best ChatGPT that $100 can buy.', stars: '57.1k', language: 'Python', updated: 'Feb 25, 2026' },
  { owner: 'colinhacks', name: 'zod', desc: 'TypeScript-first schema validation with static type inference', stars: '43.5k', language: 'TypeScript', updated: 'Feb 26, 2026' },
  { owner: 'linshenkx', name: 'prompt-optimizer', desc: 'An AI prompt optimizer for writing better prompts and getting better AI results.', stars: '33.1k', language: 'Python', updated: 'Feb 26, 2026' },
  { owner: 'eosphoros-ai', name: 'DB-GPT', desc: 'open-source agentic AI data assistant for the next generation of AI + Data products.', stars: '19.7k', language: 'Python', updated: 'Feb 24, 2026' },
  { owner: 'nextapps-de', name: 'flexsearch', desc: 'Next-generation full-text search library for Browser and Node.js', stars: '13.8k', language: 'JavaScript', updated: 'Feb 23, 2026' },
  { owner: 'Tencent', name: 'ncnn', desc: 'ncnn is a high-performance neural network inference framework optimized for the mobile platform', stars: '23.7k', language: 'C++', updated: 'Feb 25, 2026' },
  { owner: 'openai', name: 'openai-python', desc: 'The official Python library for the OpenAI API', stars: '31.3k', language: 'Python', updated: 'Feb 27, 2026' },
  { owner: 'infiniflow', name: 'ragflow', desc: 'RAGFlow is a leading open-source Retrieval-Augmented Generation (RAG) engine that fuses cutting-edge RAG with Agent capabilities to create a superior context layer for LLMs', stars: '87.4k', language: 'Python', updated: 'Mar 1, 2026' },
  { owner: 'celery', name: 'celery', desc: 'Distributed Task Queue', stars: '26.3k', language: 'Python', updated: 'Feb 22, 2026' },
  { owner: 'agent0ai', name: 'agent-zero', desc: 'Agent Zero AI framework', stars: '18.8k', language: 'Python', updated: 'Feb 24, 2026' },
  { owner: 'hackjutsu', name: 'Lepton', desc: '💻 Democratizing Snippet Management (macOS/Win/Linux)', stars: '10.3k', language: 'TypeScript', updated: 'Feb 20, 2026' },
  { owner: 'redis', name: 'redis', desc: 'Redis is an in-memory database that persists on disk.', stars: '69.1k', language: 'C', updated: 'Feb 28, 2026' },
  { owner: 'anthropics', name: 'anthropic-sdk-python', desc: 'The official Python SDK for Claude', stars: '3.8k', language: 'Python', updated: 'Feb 19, 2026' },
]

function hashOf(str) {
  let h = 0
  for (let i = 0; i < str.length; i++) h = (h * 31 + str.charCodeAt(i)) >>> 0
  return h
}

function findBySlug(owner, name) {
  return repos.find(
    (r) => r.owner.toLowerCase() === owner.toLowerCase() && r.name.toLowerCase() === name.toLowerCase()
  )
}

function parseRepo(input) {
  const slug = input.trim().replace(/^https?:\/\/(www\.)?github\.com\//, '').replace(/\/$/, '')
  const [owner, ...nameParts] = slug.split('/')
  if (!owner || nameParts.length < 1) return null
  return { owner, name: nameParts.join('/') }
}

function StarIcon({ className = '' }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M13.3602 1.8549C12.8126 0.715033 11.1861 0.715035 10.6384 1.8549L8.26986 6.78487 2.83027 7.50921C1.57091 7.68199 1.06938 9.24531 2.0075 10.1608L5.87464 13.9264 5.0253 19.3494C4.84815 20.6056 6.19992 21.557 7.31874 20.9592L12.1999 18.3895 17.0811 20.9592C18.1999 21.557 19.5517 20.6056 19.3745 19.3494L18.5252 13.9264 22.3923 10.1608C23.3304 9.24531 22.8289 7.68199 21.5695 7.50921L16.1299 6.78487 13.3602 1.8549Z" />
    </svg>
  )
}

function RepoRow({ repo, onClick }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="flex w-full items-center gap-4 px-2 py-3 text-left transition-colors hover:bg-gray-50"
    >
      <div className="flex size-10 shrink-0 items-center justify-center rounded-full border border-gray-200 bg-white text-sm font-semibold text-gray-700 shadow-sm">
        {repo.owner[0].toUpperCase()}
      </div>
      <div className="min-w-0 flex-1">
        <div className="truncate text-[15px] font-semibold text-gray-900">
          {repo.owner}/<span className="text-gray-900">{repo.name}</span>
        </div>
        <div className="truncate text-[13px] text-gray-500">{repo.desc}</div>
      </div>
      <div className="flex shrink-0 items-center gap-1 text-[13px] font-medium text-gray-500">
        <StarIcon className="size-4 text-amber-400" />
        {repo.stars}
      </div>
    </button>
  )
}

function Logo({ onClick }) {
  return (
    <button type="button" onClick={onClick} className="flex items-center gap-2">
      <svg className="size-7" viewBox="0 0 24 24" fill="none">
        <rect x="1.5" y="1.5" width="21" height="21" rx="6" fill="#11181c" />
        <path d="M7 15.5V8.5c0-.276.224-.5.5-.5h9" stroke="#fff" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M12.5 8.5c0 3.5 0 6.5 7 6.5" stroke="#fff" strokeWidth="1.6" strokeLinecap="round" />
      </svg>
      <span className="text-2xl font-bold tracking-tight">Few<span className="font-light text-gray-500">Questions</span></span>
    </button>
  )
}

function Nav({ onHome, onAdd }) {
  return (
    <nav className="sticky top-0 z-10 border-b border-gray-100 bg-white">
      <div className="mx-auto flex h-20 max-w-screen-xl items-center px-6">
        <Logo onClick={onHome} />
        <button
          type="button"
          onClick={onAdd}
          className="ml-auto inline-flex items-center gap-2 rounded-md bg-gray-900 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-gray-700"
        >
          <svg className="size-4" viewBox="0 0 20 20" fill="currentColor">
            <path d="M10.75 4.75a.75.75 0 00-1.5 0v4.5h-4.5a.75.75 0 000 1.5h4.5v4.5a.75.75 0 001.5 0v-4.5h4.5a.75.75 0 000-1.5h-4.5v-4.5z" />
          </svg>
          Add repo
        </button>
      </div>
    </nav>
  )
}

function AddRepoModal({ onClose, onSubmit }) {
  const [value, setValue] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    const repo = parseRepo(value)
    if (repo) {
      onClose()
      onSubmit(repo)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center bg-black/40 pt-32" onClick={onClose}>
      <div
        className="w-full max-w-md rounded-lg border border-gray-200 bg-white p-6 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-950">Add repo</h2>
            <p className="mt-1 text-sm text-gray-500">Paste a GitHub repo to index it.</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded p-1 text-gray-400 transition-colors hover:text-gray-700"
            aria-label="Close"
          >
            <svg className="size-5" viewBox="0 0 20 20" fill="currentColor">
              <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" />
            </svg>
          </button>
        </div>

        <form className="mt-5" onSubmit={handleSubmit}>
          <label className="block text-[13px] font-medium text-gray-700" htmlFor="repo-url">
            GitHub repo
          </label>
          <input
            id="repo-url"
            type="text"
            value={value}
            onChange={(e) => setValue(e.target.value)}
            placeholder="https://github.com/react/react"
            className="mt-1.5 w-full rounded-md border border-gray-300 px-3 py-2 text-sm outline-none transition-colors focus:border-gray-500"
            autoFocus
          />

          <div className="mt-6 flex justify-end gap-2">
            <button
              type="button"
              onClick={onClose}
              className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="rounded-md bg-gray-900 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-gray-700"
            >
              Add repo
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

function NotIndexed({ repo, onIndex }) {
  const [email, setEmail] = useState('')
  const [starting, setStarting] = useState(false)
  const [progress, setProgress] = useState(0)

  const handleIndex = (e) => {
    e.preventDefault()
    if (!email.trim() || starting) return
    setStarting(true)

    const steps = [10, 25, 45, 65, 80, 92, 100]
    steps.forEach((p, i) => {
      setTimeout(() => setProgress(p), 500 * (i + 1))
    })
    setTimeout(() => {
      setStarting(false)
      onIndex()
    }, 500 * (steps.length + 1))
  }

  return (
    <div className="rounded-lg border border-gray-200 p-6">
      <h2 className="text-base font-semibold text-gray-950">Repository Not Indexed</h2>
      <p className="mt-2 text-[14px] leading-relaxed text-gray-600">
        This repository hasn't been indexed yet.
      </p>

      {!starting && progress === 0 && (
        <form className="mt-5" onSubmit={handleIndex}>
          <label className="block text-[13px] font-medium text-gray-700" htmlFor="email">
            Email to notify
          </label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            className="mt-1.5 w-full max-w-sm rounded-md border border-gray-300 px-3 py-2 text-sm outline-none transition-colors focus:border-gray-500"
          />
          <div className="mt-4">
            <button
              type="submit"
              disabled={!email.trim()}
              className="rounded-md bg-gray-900 px-5 py-2 text-sm font-medium text-white transition-colors hover:bg-gray-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Index Repository
            </button>
          </div>
        </form>
      )}

      {starting && (
        <div className="mt-6">
          <div className="h-2 w-full overflow-hidden rounded-full bg-gray-200">
            <div
              className="h-full rounded-full bg-emerald-500 transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
          <p className="mt-3 text-[13px] text-gray-600">
            Indexing {repo.owner}/{repo.name}… {progress}%
          </p>
        </div>
      )}

      {!starting && progress === 100 && (
        <div className="mt-4 flex items-center gap-2 text-sm font-medium text-emerald-600">
          <span className="flex size-5 items-center justify-center rounded-full bg-emerald-100">
            <svg className="size-3" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M16.7 5.3a1 1 0 010 1.4l-8 8a1 1 0 01-1.4 0l-4-4a1 1 0 111.4-1.4L8 12.6l7.3-7.3a1 1 0 011.4 0z" clipRule="evenodd" />
            </svg>
          </span>
          Indexed! You can now explore and search this repository.
        </div>
      )}

      <p className="mt-6 border-t border-gray-100 pt-4 text-[13px] text-gray-500">
        Indexing typically takes 2–10 minutes to complete after it starts indexing.
      </p>
    </div>
  )
}

function RepoPage({ repo, indexed, onIndexed }) {
  const meta = indexed
    ? findBySlug(repo.owner, repo.name) || {
        ...repo,
        desc: '',
        stars: '—',
        language: '—',
        updated: '—',
      }
    : { ...repo, desc: '', stars: '—', language: '—', updated: '—' }

  return (
    <main className="mx-auto max-w-3xl px-6 py-10">
      <div className="flex items-start gap-5">
        <div className="flex size-20 shrink-0 items-center justify-center rounded-2xl border border-gray-200 bg-gray-50 text-3xl font-bold text-gray-800">
          {meta.owner[0].toUpperCase()}
        </div>
        <div className="min-w-0 flex-1">
          <h1 className="truncate text-3xl font-bold tracking-tight text-gray-950">
            {meta.name}
          </h1>
          <div className="mt-1 font-mono text-[15px] text-gray-500">
            {meta.owner}/{meta.name}
          </div>
          {meta.desc && <p className="mt-3 text-[15px] leading-relaxed text-gray-700">{meta.desc}</p>}
          <div className="mt-4 flex flex-wrap items-center gap-x-5 gap-y-1.5 text-[13px] text-gray-600">
            <span className="flex items-center gap-1.5">
              <span className="size-3 rounded-full bg-emerald-500" />
              <span className="font-medium">{meta.language}</span>
            </span>
            <span className="flex items-center gap-1.5">
              <StarIcon className="size-4 text-amber-400" />
              <span className="font-medium">{meta.stars}</span>
              stars
            </span>
            <span className="text-gray-400">Updated: {meta.updated}</span>
          </div>
        </div>
      </div>

      <div className="mt-10">
        <NotIndexed key={`${meta.owner}/${meta.name}`} repo={meta} onIndex={() => onIndexed(meta)} />
      </div>
    </main>
  )
}

function Home({ onOpenRepo }) {
  const [query, setQuery] = useState('')
  const inputRef = useRef(null)

  const filtered = repos.filter(
    (r) =>
      !query ||
      `${r.owner}/${r.name}`.toLowerCase().includes(query.toLowerCase())
  )

  const handleSubmit = (e) => {
    e.preventDefault()
    const repo = parseRepo(query)
    if (repo) {
      setQuery('')
      onOpenRepo(repo)
    }
  }

  return (
    <main className="mx-auto max-w-3xl px-6">
      <section className="pt-16 pb-8 text-center">
        <h1 className="text-balance text-4xl font-bold tracking-tight text-gray-950 sm:text-5xl">
          Which repo would you like to play with?
        </h1>

        <form className="mx-auto mt-8 max-w-2xl" onSubmit={handleSubmit}>
          <div className="flex items-center overflow-hidden border border-gray-300 bg-white focus-within:border-gray-500">
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Add repo… e.g. react/react"
              className="w-full bg-transparent px-4 py-3.5 text-[15px] outline-none placeholder:text-gray-400"
            />
            <button
              type="submit"
              className="shrink-0 bg-gray-900 px-5 py-3 text-white transition-colors hover:bg-gray-700"
            >
              <svg className="size-4" viewBox="0 0 20 20" fill="none">
                <path d="M3 10h12M10 5l5 5-5 5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </button>
          </div>
        </form>
      </section>

      <section className="pb-24">
        {filtered.length > 0 ? (
          <div>
            {filtered.map((repo) => (
              <RepoRow
                key={`${repo.owner}/${repo.name}`}
                repo={repo}
                onClick={() => onOpenRepo(repo)}
              />
            ))}
          </div>
        ) : (
          <p className="py-8 text-center text-sm text-gray-400">
            No repos match "{query}". Try another name.
          </p>
        )}
      </section>

      <section className="border-t border-gray-100 pb-24 pt-12 text-center">
        <h2 className="text-xl font-semibold text-gray-950">What is FewQuestions?</h2>
        <p className="mx-auto mt-3 max-w-lg text-[15px] text-gray-500">
          FewQuestions provides questions to get a better active understanding of
          the repo, rather than passively reading the code or theory about it.
        </p>
      </section>
    </main>
  )
}

function App() {
  const [current, setCurrent] = useState(null)
  const [showAdd, setShowAdd] = useState(false)

  const openRepo = (repo) => setCurrent(repo)
  const goHome = () => setCurrent(null)

  const handleIndexed = (repo) => {
    repos.unshift({ ...repo, stars: '—', language: 'Python', updated: 'Just now' })
    setCurrent({ ...repo, indexState: 'just-indexed' })
  }

  const indexedSlug = current && findBySlug(current.owner, current.name)

  return (
    <div className="min-h-screen bg-white text-gray-900">
      <Nav
        onHome={goHome}
        onAdd={() => setShowAdd(true)}
      />

      {current ? (
        <RepoPage
          repo={current}
          indexed={!!indexedSlug}
          onIndexed={handleIndexed}
        />
      ) : (
        <Home onOpenRepo={openRepo} />
      )}

      {showAdd && (
        <AddRepoModal
          onClose={() => setShowAdd(false)}
          onSubmit={(repo) => {
            setShowAdd(false)
            openRepo(repo)
          }}
        />
      )}
    </div>
  )
}

export default App