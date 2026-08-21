import { useEffect, useRef, useState } from 'react'
import { fetchRepos, prepareRepo, fetchQuestions } from './api'

function parseRepo(input) {
  const slug = input.trim().replace(/^https?:\/\/(www\.)?github\.com\//, '').replace(/\/$/, '')
  const [owner, ...nameParts] = slug.split('/')
  if (!owner || nameParts.length < 1) return null
  return { owner, name: nameParts.join('/') }
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

function Nav({ onHome, onAdd, disabled }) {
  return (
    <nav className="sticky top-0 z-10 border-b border-gray-100 bg-white">
      <div className="mx-auto flex h-20 max-w-screen-xl items-center px-6">
        <Logo onClick={onHome} />
        <button
          type="button"
          onClick={onAdd}
          disabled={disabled}
          className="ml-auto inline-flex items-center gap-2 rounded-md bg-gray-900 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-gray-700 disabled:cursor-not-allowed disabled:opacity-50"
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
      <div className="w-full max-w-md rounded-lg border border-gray-200 bg-white p-6 shadow-xl" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-950">Add repo</h2>
            <p className="mt-1 text-sm text-gray-500">Paste a GitHub repo to index it.</p>
          </div>
          <button type="button" onClick={onClose} className="rounded p-1 text-gray-400 hover:text-gray-700" aria-label="Close">
            <svg className="size-5" viewBox="0 0 20 20" fill="currentColor">
              <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" />
            </svg>
          </button>
        </div>
        <form className="mt-5" onSubmit={handleSubmit}>
          <label className="block text-[13px] font-medium text-gray-700" htmlFor="repo-url">GitHub repo</label>
          <input
            id="repo-url"
            type="text"
            value={value}
            onChange={(e) => setValue(e.target.value)}
            placeholder="https://github.com/react/react"
            className="mt-1.5 w-full rounded-md border border-gray-300 px-3 py-2 text-sm outline-none focus:border-gray-500"
            autoFocus
          />
          <div className="mt-6 flex justify-end gap-2">
            <button type="button" onClick={onClose} className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50">Cancel</button>
            <button type="submit" className="rounded-md bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-700">Add repo</button>
          </div>
        </form>
      </div>
    </div>
  )
}

function Spinner({ className = 'size-4' }) {
  return (
    <svg className={`${className} animate-spin`} viewBox="0 0 24 24" fill="none">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
    </svg>
  )
}

function IndexPanel({ repo }) {
  const [phase, setPhase] = useState('idle') // idle | preparing | generating | done | error
  const [questions, setQuestions] = useState([])
  const [error, setError] = useState(null)
  const [page, setPage] = useState(0)
  const pageSize = 8

  const repoUrl = `https://github.com/${repo.owner}/${repo.name}`
  const isBusy = phase === 'preparing' || phase === 'generating'
  const totalPages = Math.max(1, Math.ceil(questions.length / pageSize))
  const paged = questions.slice(page * pageSize, (page + 1) * pageSize)

  const start = async () => {
    if (isBusy) return
    setError(null)
    setQuestions([])
    setPage(0)
    try {
      setPhase('preparing')
      await prepareRepo({ repoUrl })
      setPhase('generating')
      const res = await fetchQuestions({ repoUrl })
      setQuestions(res.questions || [])
      setPhase('done')
    } catch (e) {
      setError(e.message || 'Something went wrong')
      setPhase('error')
    }
  }

  const retry = () => {
    setError(null)
    setPhase('idle')
  }

  return (
    <div className="rounded-lg border border-gray-200 p-6">
      {phase === 'idle' && (
        <>
          <h2 className="text-base font-semibold text-gray-950">Repository Not Indexed</h2>
          <p className="mt-2 text-[14px] leading-relaxed text-gray-600">This repository hasn't been indexed yet. Indexing clones and embeds the code locally — next time it's instant.</p>
          <button
            type="button"
            onClick={start}
            className="mt-5 rounded-md bg-gray-900 px-5 py-2 text-sm font-medium text-white hover:bg-gray-700"
          >
            Index Repository
          </button>
          <p className="mt-4 text-[13px] text-gray-500">Indexing takes 2–10 minutes on first run. Generating questions takes ~30s after that.</p>
        </>
      )}

      {isBusy && (
        <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
          <div className="flex items-start gap-4">
            <div className="flex size-10 shrink-0 items-center justify-center rounded-full bg-gray-900 text-white shadow-sm">
              <Spinner className="size-5" />
            </div>
            <div className="min-w-0 flex-1">
              <h3 className="text-sm font-semibold tracking-tight text-gray-950">
                {phase === 'preparing' ? `Indexing ${repo.owner}/${repo.name}` : 'Crafting questions'}
              </h3>
              <p className="mt-1 text-sm leading-relaxed text-gray-500">
                {phase === 'preparing'
                  ? 'Cloning and embedding the codebase. First run takes a bit — next time it’s instant from cache.'
                  : 'Turning the indexed code into 30–40 questions for you.'}
              </p>
            </div>
            <span className="hidden sm:inline-flex items-center rounded-full bg-gray-50 px-2.5 py-1 text-xs font-medium text-gray-500 ring-1 ring-inset ring-gray-200">
              <span className="mr-1.5 size-2 animate-pulse rounded-full bg-amber-400" />
              Working
            </span>
          </div>

          <div className="mt-6 space-y-3">
            <div className="flex items-center gap-3">
              <span className={`flex size-7 shrink-0 items-center justify-center rounded-full text-xs font-semibold ring-1 ${phase === 'preparing' ? 'bg-gray-900 text-white ring-gray-900' : 'bg-emerald-500 text-white ring-emerald-500'}`}>
                {phase === 'preparing' ? <Spinner className="size-3.5" /> : '✓'}
              </span>
              <span className={`text-sm ${phase === 'preparing' ? 'font-medium text-gray-900' : 'text-gray-600'}`}>Index & embed repository</span>
              <span className="ml-auto hidden sm:block text-xs text-gray-400">2–10 min first run</span>
            </div>
            <div className="flex items-center gap-3">
              <span className={`flex size-7 shrink-0 items-center justify-center rounded-full text-xs font-semibold ring-1 ${phase === 'generating' ? 'bg-gray-900 text-white ring-gray-900' : 'bg-white text-gray-400 ring-gray-200'}`}>
                {phase === 'generating' ? <Spinner className="size-3.5" /> : '2'}
              </span>
              <span className={`text-sm ${phase === 'generating' ? 'font-medium text-gray-900' : 'text-gray-400'}`}>Craft 30–40 hypotheses</span>
              <span className="ml-auto hidden sm:block text-xs text-gray-400">~30s</span>
            </div>
          </div>

          <div className="mt-6 h-1.5 w-full overflow-hidden rounded-full bg-gray-100">
            <div className="h-full w-1/2 rounded-full bg-gradient-to-r from-gray-900 via-gray-600 to-gray-900 animate-pulse" />
          </div>
          <p className="mt-3 text-center text-xs text-gray-400">Buttons are disabled until it finishes — please keep this tab open.</p>
        </div>
      )}

      {phase === 'error' && (
        <>
          <h2 className="text-base font-semibold text-red-700">Failed to index</h2>
          <p className="mt-2 text-sm text-red-600 break-words">{error}</p>
          <button type="button" onClick={retry} className="mt-4 rounded-md bg-gray-900 px-5 py-2 text-sm font-medium text-white hover:bg-gray-700">Try again</button>
        </>
      )}

      {phase === 'done' && (
        <div className="rounded-xl border border-gray-200 bg-white shadow-sm overflow-hidden">
          <div className="flex items-center justify-between border-b border-gray-100 bg-gray-50/50 px-6 py-4">
            <h3 className="text-sm font-semibold tracking-tight text-gray-950">{questions.length} questions</h3>
            <span className="text-xs text-gray-400">
              {page * pageSize + 1}–{Math.min((page + 1) * pageSize, questions.length)} of {questions.length}
            </span>
          </div>

          {questions.length > 0 ? (
            <>
              <ul className="divide-y divide-gray-100">
                {paged.map((q) => (
                <li key={q.id} className="group px-6 py-4 hover:bg-gray-50/70 transition-colors">
                  <div className="flex gap-4">
                    <span className="flex size-8 shrink-0 items-center justify-center rounded-full bg-gray-900 text-xs font-semibold text-white shadow-sm">
                      {String(q.id).padStart(2, '0')}
                    </span>
                    <p className="flex-1 pt-1 text-[14px] font-medium leading-relaxed text-gray-900">
                      {q.question}
                    </p>
                  </div>
                  {(q.target_files?.length > 0 || q.target_functions?.length > 0) && (
                    <div className="mt-3 ml-12 flex flex-wrap gap-1.5">
                      {q.target_files?.map((f) => (
                        <span key={f} className="inline-flex items-center gap-1 rounded-full bg-white px-2.5 py-1 text-xs font-medium text-gray-700 ring-1 ring-inset ring-gray-200">
                          <svg className="size-3 text-gray-400" viewBox="0 0 20 20" fill="none"><path d="M4 6.5A1.5 1.5 0 015.5 5h3.379a1 1 0 01.894.553l.448.894A1 1 0 007.33 7H5.5A1.5 1.5 0 004 8.5v7A1.5 1.5 0 005.5 17h9a1.5 1.5 0 001.5-1.5v-8A1.5 1.5 0 0014.5 6h-2.621a1 1 0 01-.894-.553l-.448-.894A1 1 0 0010.379 4H5.5A1.5 1.5 0 004 5.5v1z" stroke="currentColor" strokeWidth="1.3" /></svg>
                          {f}
                        </span>
                      ))}
                      {q.target_functions?.map((fn) => (
                        <span key={fn} className="inline-flex items-center rounded-full bg-gray-900 px-2.5 py-1 text-xs font-mono font-medium text-white">
                          {fn}()
                        </span>
                      ))}
                    </div>
                  )}
                </li>
              ))}
            </ul>
            {totalPages > 1 && (
              <div className="flex items-center justify-between border-t border-gray-100 bg-gray-50/30 px-6 py-3">
                <button
                  type="button"
                  onClick={() => setPage((p) => Math.max(0, p - 1))}
                  disabled={page === 0}
                  className="rounded-md border border-gray-200 bg-white px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  ← Previous
                </button>
                <span className="text-xs text-gray-500">Page {page + 1} of {totalPages}</span>
                <button
                  type="button"
                  onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
                  disabled={page + 1 >= totalPages}
                  className="rounded-md border border-gray-200 bg-white px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  Next →
                </button>
              </div>
            )}
            </>
          ) : (
            <p className="px-6 py-8 text-center text-sm text-gray-500">No questions returned.</p>
          )}
        </div>
      )}
    </div>
  )
}

function RepoPage({ repo }) {
  return (
    <main className="mx-auto max-w-3xl px-6 py-10">
      <div className="flex items-start gap-5">
        <div className="flex size-20 shrink-0 items-center justify-center rounded-2xl border border-gray-200 bg-gray-50 text-3xl font-bold text-gray-800">
          {repo.owner[0].toUpperCase()}
        </div>
        <div className="min-w-0 flex-1">
          <h1 className="truncate text-3xl font-bold tracking-tight text-gray-950">{repo.name}</h1>
          <div className="mt-1 font-mono text-[15px] text-gray-500">{repo.owner}/{repo.name}</div>
        </div>
      </div>
      <div className="mt-10">
        <IndexPanel key={`${repo.owner}/${repo.name}`} repo={repo} />
      </div>
    </main>
  )
}

function Home({ onOpenRepo }) {
  const [query, setQuery] = useState('')
  const [cached, setCached] = useState([])
  const [loadingCached, setLoadingCached] = useState(true)
  const inputRef = useRef(null)

  useEffect(() => {
    let cancelled = false
    fetchRepos()
      .then((res) => {
        if (!cancelled) setCached(res.repos || [])
      })
      .catch(() => {})
      .finally(() => {
        if (!cancelled) setLoadingCached(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

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
        <h1 className="text-balance text-4xl font-bold tracking-tight text-gray-950 sm:text-5xl">Which repo would you like to play with?</h1>
        <form className="mx-auto mt-8 max-w-2xl" onSubmit={handleSubmit}>
          <div className="flex items-center overflow-hidden border border-gray-300 bg-white focus-within:border-gray-500">
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="https://github.com/react/react"
              className="w-full bg-transparent px-4 py-3.5 text-[15px] outline-none placeholder:text-gray-400"
            />
            <button type="submit" className="shrink-0 bg-gray-900 px-5 py-3 text-white hover:bg-gray-700">
              <svg className="size-4" viewBox="0 0 20 20" fill="none"><path d="M3 10h12M10 5l5 5-5 5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" /></svg>
            </button>
          </div>
        </form>
      </section>

      {cached.length > 0 && (
        <section className="pb-10">
          <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
            {cached.map((r) => (
              <button
                key={r.slug}
                onClick={() => onOpenRepo({ owner: r.owner, name: r.name })}
                className="flex w-full items-center gap-4 px-4 py-3.5 text-left hover:bg-gray-50 transition-colors border-b border-gray-100 last:border-0"
              >
                <div className="flex size-9 shrink-0 items-center justify-center rounded-full bg-gray-900 text-xs font-semibold text-white">
                  {r.owner[0].toUpperCase()}
                </div>
                <div className="min-w-0 flex-1 truncate text-sm font-medium text-gray-900">{r.owner}/{r.name}</div>
                <svg className="size-4 shrink-0 text-gray-400" viewBox="0 0 20 20" fill="none"><path d="M7 10h8M11 6l4 4-4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" /></svg>
              </button>
            ))}
          </div>
        </section>
      )}

      {loadingCached && cached.length === 0 && <div className="pb-10 text-center text-xs text-gray-400">Checking cached repos…</div>}

      <section className="border-t border-gray-100 pb-24 pt-12 text-center">
        <h2 className="text-xl font-semibold text-gray-950">What is FewQuestions?</h2>
        <p className="mx-auto mt-3 max-w-lg text-[15px] text-gray-500">FewQuestions gives you 30-40 testable hypotheses to actively investigate a repo, rather than passively reading it.</p>
      </section>
    </main>
  )
}

function App() {
  const [current, setCurrent] = useState(null)
  const [showAdd, setShowAdd] = useState(false)
  const openRepo = (repo) => setCurrent(repo)
  const goHome = () => setCurrent(null)
  const isBusyOnRepoPage = false // App-level nav stays enabled; IndexPanel disables its own button while busy

  return (
    <div className="min-h-screen bg-white text-gray-900">
      <Nav onHome={goHome} onAdd={() => setShowAdd(true)} disabled={isBusyOnRepoPage} />
      {current ? <RepoPage repo={current} /> : <Home onOpenRepo={openRepo} />}
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
