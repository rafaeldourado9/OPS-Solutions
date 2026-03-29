import { useState, useRef, useEffect, useCallback } from 'react'
import { useInfiniteQuery, useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  ChatCircleDots, MagnifyingGlass, Robot, User, ArrowLeft,
  SpinnerGap, ArrowUp, PaperPlaneTilt, Warning, Trash,
  PencilSimple, Check, X,
} from '@phosphor-icons/react'
import { conversationsApi, type Conversation, type Message } from '../../api/conversations'
import { agentsApi, type AgentInstance } from '../../api/agents'

// ─── Constants ────────────────────────────────────────────────────────────────

const MSG_PAGE_SIZE = 50
const CONV_PAGE_SIZE = 30

// ─── Helpers ──────────────────────────────────────────────────────────────────

const AVATAR_COLORS = [
  'bg-[#0ABAB5]', 'bg-violet-500', 'bg-orange-500',
  'bg-rose-500',  'bg-blue-500',   'bg-emerald-600',
]

function getInitials(name: string) {
  return name.split(' ').filter(Boolean).slice(0, 2).map(w => w[0]).join('').toUpperCase() || '?'
}

function Avatar({ name, size = 'md' }: { name: string; size?: 'sm' | 'md' }) {
  const v = getInitials(name)
  const c = AVATAR_COLORS[v.charCodeAt(0) % AVATAR_COLORS.length]
  const sz = size === 'sm' ? 'w-8 h-8 text-[11px]' : 'w-10 h-10 text-sm'
  return (
    <div className={`${sz} ${c} rounded-full flex items-center justify-center text-white font-bold shrink-0`}>
      {v}
    </div>
  )
}

function fmtListTime(ts?: string) {
  if (!ts) return ''
  const d = new Date(ts)
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  if (diff < 86_400_000) return d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
  if (diff < 604_800_000) return d.toLocaleDateString('pt-BR', { weekday: 'short' })
  return d.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' })
}

function fmtMsgTime(ts: string) {
  return new Date(ts).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
}

function dateSeparatorLabel(ts: string) {
  const d = new Date(ts)
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  if (diff < 86_400_000 && d.getDate() === now.getDate()) return 'Hoje'
  if (diff < 172_800_000) return 'Ontem'
  return d.toLocaleDateString('pt-BR', { weekday: 'long', day: '2-digit', month: 'long' })
}

// ─── WebSocket hook ────────────────────────────────────────────────────────────

function useConversationsWS(onEvent: (event: { type: string; data: any }) => void) {
  const wsRef = useRef<WebSocket | null>(null)
  const retryRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const backoffRef = useRef(1000)

  useEffect(() => {
    let destroyed = false

    function connect() {
      if (destroyed) return
      try {
        const raw = localStorage.getItem('ops-auth')
        const token = raw ? JSON.parse(raw)?.state?.token : null
        if (!token) return

        const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
        const ws = new WebSocket(`${proto}//${window.location.host}/ws/conversations?token=${token}`)
        wsRef.current = ws

        ws.onopen = () => {
          backoffRef.current = 1000 // reset on success
        }

        ws.onmessage = (e) => {
          try { onEvent(JSON.parse(e.data)) } catch { /* ignore malformed */ }
        }

        // keep-alive ping every 25s
        const ping = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify({ type: 'ping' }))
        }, 25_000)

        ws.onclose = () => {
          clearInterval(ping)
          if (!destroyed) {
            retryRef.current = setTimeout(connect, backoffRef.current)
            backoffRef.current = Math.min(backoffRef.current * 2, 30_000)
          }
        }

        ws.onerror = () => { ws.close() }
      } catch {
        if (!destroyed) {
          retryRef.current = setTimeout(connect, backoffRef.current)
          backoffRef.current = Math.min(backoffRef.current * 2, 30_000)
        }
      }
    }

    connect()

    return () => {
      destroyed = true
      if (retryRef.current) clearTimeout(retryRef.current)
      wsRef.current?.close()
    }
  }, [onEvent])
}

// ─── Conversation list sidebar ─────────────────────────────────────────────────

interface SidebarProps {
  selectedId: string | null
  onSelect: (chatId: string) => void
  onDeselect: () => void
  search: string
  onSearchChange: (v: string) => void
  agentId: string | null
}

function ConversationSidebar({ selectedId, onSelect, onDeselect, search, onSearchChange, agentId }: SidebarProps) {
  const queryClient = useQueryClient()
  const sentinelRef = useRef<HTMLDivElement>(null)

  const deleteMutation = useMutation({
    mutationFn: ({ chatId, agentId }: { chatId: string; agentId: string }) =>
      conversationsApi.deleteConversation(chatId, agentId),
    onSuccess: (_, { chatId }) => {
      if (selectedId === chatId) onDeselect()
      queryClient.invalidateQueries({ queryKey: ['conversations'] })
    },
  })

  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    isLoading,
  } = useInfiniteQuery({
    queryKey: ['conversations', agentId],
    queryFn: ({ pageParam = 0 }) =>
      conversationsApi.list({ offset: pageParam as number, limit: CONV_PAGE_SIZE, agent_id: agentId ?? undefined }),
    getNextPageParam: (last) => {
      const loaded = last.offset + last.items.length
      return loaded < last.total ? loaded : undefined
    },
    initialPageParam: 0,
    refetchInterval: 30_000, // fallback polling if WS misses something
  })

  const allConvs = data?.pages.flatMap(p => p.items) ?? []
  const filtered = search
    ? allConvs.filter(c =>
        c.customer_name.toLowerCase().includes(search.toLowerCase()) ||
        c.customer_phone.includes(search)
      )
    : allConvs

  // IntersectionObserver to load more conversations when scrolling to bottom
  useEffect(() => {
    if (!sentinelRef.current || !hasNextPage) return
    const obs = new IntersectionObserver(
      entries => { if (entries[0].isIntersecting && !isFetchingNextPage) fetchNextPage() },
      { threshold: 0.1 }
    )
    obs.observe(sentinelRef.current)
    return () => obs.disconnect()
  }, [hasNextPage, isFetchingNextPage, fetchNextPage])



  return (
    <div className="flex flex-col h-full">
      <div className="p-4 border-b border-zinc-100 shrink-0 space-y-2.5">
        <h2 className="text-[15px] font-bold text-[#1D1D1F]">Conversas</h2>

        <div className="flex items-center gap-2 bg-zinc-50 border border-zinc-200 rounded-xl px-3 py-2 focus-within:border-[#0ABAB5]/50 transition-all">
          <MagnifyingGlass size={14} className="text-zinc-400 shrink-0" />
          <input
            value={search}
            onChange={e => onSearchChange(e.target.value)}
            placeholder="Buscar conversas..."
            className="text-[13px] bg-transparent focus:outline-none w-full placeholder:text-zinc-400"
          />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="flex items-center justify-center py-16">
            <SpinnerGap size={24} className="animate-spin text-[#0ABAB5]" />
          </div>
        ) : filtered.length === 0 ? (
          <div className="flex flex-col items-center py-16 text-zinc-300">
            <ChatCircleDots size={36} weight="duotone" />
            <p className="text-sm mt-2 text-zinc-400">
              {search ? 'Nenhuma conversa encontrada' : 'Nenhuma conversa ainda'}
            </p>
          </div>
        ) : (
          <>
            {filtered.map(c => (
              <ConversationItem
                key={c.chat_id}
                conv={c}
                selected={selectedId === c.chat_id}
                onSelect={onSelect}
                onDelete={() => deleteMutation.mutate({ chatId: c.chat_id, agentId: c.agent_id })}
              />
            ))}
            <div ref={sentinelRef} className="h-4" />
            {isFetchingNextPage && (
              <div className="flex justify-center py-3">
                <SpinnerGap size={16} className="animate-spin text-zinc-400" />
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}

const SWIPE_THRESHOLD = 72  // px to reveal delete button
const SWIPE_DELETE    = 200 // px to auto-delete

function ConversationItem({
  conv, selected, onSelect, onDelete,
}: { conv: Conversation; selected: boolean; onSelect: (id: string) => void; onDelete: () => void }) {
  const [offset, setOffset] = useState(0)
  const [animating, setAnimating] = useState(false)
  const startXRef = useRef<number | null>(null)
  const movedRef = useRef(false)
  const containerRef = useRef<HTMLDivElement>(null)

  function handlePointerDown(e: React.PointerEvent) {
    startXRef.current = e.clientX
    movedRef.current = false
  }

  function handlePointerMove(e: React.PointerEvent) {
    if (startXRef.current === null) return
    const dx = Math.min(0, e.clientX - startXRef.current) // only left
    if (Math.abs(dx) > 5) movedRef.current = true
    setOffset(dx)
  }

  function handlePointerUp() {
    if (startXRef.current === null) return
    startXRef.current = null
    if (offset <= -SWIPE_DELETE) {
      // Animate out and delete
      setAnimating(true)
      setOffset(-400)
      setTimeout(onDelete, 280)
    } else if (offset <= -SWIPE_THRESHOLD) {
      setOffset(-SWIPE_THRESHOLD) // snap open
    } else {
      setOffset(0) // snap back
    }
  }

  function handleDeleteClick(e: React.MouseEvent) {
    e.stopPropagation()
    setAnimating(true)
    setOffset(-400)
    setTimeout(onDelete, 280)
  }

  const revealed = offset <= -SWIPE_THRESHOLD

  return (
    <div
      ref={containerRef}
      className="relative overflow-hidden select-none"
      style={{ touchAction: 'pan-y' }}
      onPointerDown={handlePointerDown}
      onPointerMove={handlePointerMove}
      onPointerUp={handlePointerUp}
      onPointerCancel={handlePointerUp}
    >
      {/* Delete background */}
      <div
        className={`absolute inset-y-0 right-0 flex items-center justify-center bg-red-500 transition-opacity ${revealed ? 'opacity-100' : 'opacity-0'}`}
        style={{ width: SWIPE_THRESHOLD }}
      >
        <button
          onPointerDown={e => e.stopPropagation()}
          onClick={handleDeleteClick}
          className="flex flex-col items-center gap-1 text-white"
        >
          <Trash size={18} weight="bold" />
          <span className="text-[10px] font-semibold">Apagar</span>
        </button>
      </div>

      {/* Conversation row */}
      <button
        onClick={() => { if (!movedRef.current && offset === 0) onSelect(conv.chat_id); else { setOffset(0); movedRef.current = false } }}
        style={{
          transform: `translateX(${offset}px)`,
          transition: animating || startXRef.current === null ? 'transform 0.25s ease' : 'none',
        }}
        className={`w-full flex items-start gap-3 px-4 py-3.5 text-left bg-white border-l-2 ${
          selected ? 'bg-[#0ABAB5]/8 border-[#0ABAB5]' : 'hover:bg-zinc-50 border-transparent'
        }`}
      >
        <div className="relative shrink-0">
          <Avatar name={conv.customer_name} />
          {conv.status === 'active' && (
            <span className="absolute bottom-0 right-0 w-2.5 h-2.5 bg-emerald-400 rounded-full border-2 border-white" />
          )}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2 mb-0.5">
            <div className="flex items-center gap-1.5 min-w-0">
              <p className="text-[13px] font-semibold text-[#1D1D1F] truncate">{conv.customer_name}</p>
              {conv.takeover_active && (
                <span className="shrink-0 flex items-center gap-0.5 text-[9px] font-bold text-orange-600 bg-orange-50 px-1.5 py-0.5 rounded-full border border-orange-100">
                  <User size={8} weight="bold" />HUMANO
                </span>
              )}
            </div>
            <span className="text-[11px] text-zinc-400 shrink-0">{fmtListTime(conv.last_message_at)}</span>
          </div>
          <div className="flex items-center justify-between gap-2">
            <p className="text-[12px] text-zinc-400 truncate">{conv.last_message ?? ''}</p>
            {conv.unread_count > 0 && (
              <span className="shrink-0 min-w-[20px] h-5 rounded-full bg-[#0ABAB5] text-white text-[10px] font-bold flex items-center justify-center px-1.5">
                {conv.unread_count > 99 ? '99+' : conv.unread_count}
              </span>
            )}
          </div>
        </div>
      </button>
    </div>
  )
}

// ─── Chat Area ─────────────────────────────────────────────────────────────────

interface ChatAreaProps {
  conv: Conversation
  onBack: () => void
}

function ChatArea({ conv, onBack }: ChatAreaProps) {
  const queryClient = useQueryClient()
  const scrollAreaRef = useRef<HTMLDivElement>(null)
  const topSentinelRef = useRef<HTMLDivElement>(null)
  const prevScrollHeightRef = useRef(0)
  const isAtBottomRef = useRef(true)
  const [message, setMessage] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Local takeover state — updates immediately on mutation, syncs from prop
  const [takeoverActive, setTakeoverActive] = useState(conv.takeover_active)
  useEffect(() => { setTakeoverActive(conv.takeover_active) }, [conv.takeover_active])

  // Inline rename state
  const [editingName, setEditingName] = useState(false)
  const [nameValue, setNameValue] = useState(conv.customer_name)
  useEffect(() => { setNameValue(conv.customer_name) }, [conv.customer_name])

  // ── Lazy-load messages: DESC order → newest first → pages reversed for display
  const {
    data: pages,
    fetchNextPage: fetchOlder,
    hasNextPage: hasOlder,
    isFetchingNextPage: isFetchingOlder,
    isLoading: msgsLoading,
  } = useInfiniteQuery({
    queryKey: ['messages', conv.chat_id, conv.agent_id],
    queryFn: ({ pageParam = 0 }) =>
      conversationsApi.getMessages(conv.chat_id, {
        offset: pageParam as number,
        limit: MSG_PAGE_SIZE,
        order: 'desc',
        agent_id: conv.agent_id || undefined,
      }),
    getNextPageParam: (last) => {
      const loaded = last.offset + last.items.length
      return loaded < last.total ? loaded : undefined
    },
    initialPageParam: 0,
    staleTime: 0,
    refetchInterval: 3_000, // fast polling fallback if WS misses something
  })

  // Combine pages: DESC pages reversed → chronological order for display
  const allMessages: Message[] = pages
    ? pages.pages
        .slice()
        .reverse()
        .flatMap(p => [...p.items].reverse())
    : []

  // ── Scroll to bottom on initial load or new messages
  useEffect(() => {
    if (!scrollAreaRef.current || msgsLoading) return
    if (isAtBottomRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight
    }
  }, [allMessages.length, msgsLoading])

  // ── Track if user is near bottom
  function handleScroll() {
    const el = scrollAreaRef.current
    if (!el) return
    isAtBottomRef.current = el.scrollHeight - el.scrollTop - el.clientHeight < 80
  }

  // ── Preserve scroll position when loading older messages
  useEffect(() => {
    if (!isFetchingOlder && prevScrollHeightRef.current && scrollAreaRef.current) {
      const diff = scrollAreaRef.current.scrollHeight - prevScrollHeightRef.current
      scrollAreaRef.current.scrollTop = diff
      prevScrollHeightRef.current = 0
    }
  }, [isFetchingOlder])

  // ── IntersectionObserver at top — loads older messages
  useEffect(() => {
    if (!topSentinelRef.current || !hasOlder) return
    const obs = new IntersectionObserver(
      entries => {
        if (entries[0].isIntersecting && !isFetchingOlder) {
          prevScrollHeightRef.current = scrollAreaRef.current?.scrollHeight ?? 0
          fetchOlder()
        }
      },
      { root: scrollAreaRef.current, threshold: 0.1 }
    )
    obs.observe(topSentinelRef.current)
    return () => obs.disconnect()
  }, [hasOlder, isFetchingOlder, fetchOlder])

  // ── Mutations
  const takeoverMutation = useMutation({
    mutationFn: () => conversationsApi.startTakeover(conv.chat_id, conv.agent_id || undefined),
    onSuccess: () => {
      setTakeoverActive(true)
      queryClient.invalidateQueries({ queryKey: ['conversations'] })
    },
  })

  const endTakeoverMutation = useMutation({
    mutationFn: () => conversationsApi.endTakeover(conv.chat_id, conv.agent_id || undefined),
    onSuccess: () => {
      setTakeoverActive(false)
      queryClient.invalidateQueries({ queryKey: ['conversations'] })
    },
  })

  const renameMutation = useMutation({
    mutationFn: (name: string) => conversationsApi.renameContact(conv.chat_id, name, conv.agent_id || undefined),
    onSuccess: () => {
      setEditingName(false)
      queryClient.invalidateQueries({ queryKey: ['conversations'] })
    },
  })

  function handleRenameSubmit() {
    const trimmed = nameValue.trim()
    if (trimmed && trimmed !== conv.customer_name) renameMutation.mutate(trimmed)
    else setEditingName(false)
  }

  const sendMutation = useMutation({
    mutationFn: (content: string) => conversationsApi.sendMessage(conv.chat_id, content, conv.agent_id || undefined),
    onSuccess: (newMsg) => {
      // Add to cache with dedup check
      queryClient.setQueryData(['messages', conv.chat_id, conv.agent_id], (old: any) => {
        if (!old) return old
        const pages = [...old.pages]
        const firstPage = { ...pages[0] }
        // Avoid duplicates (WS event may have already added this)
        if (firstPage.items?.some((m: any) => m.id === newMsg.id)) return old
        firstPage.items = [newMsg, ...(firstPage.items || [])]
        firstPage.total = (firstPage.total || 0) + 1
        pages[0] = firstPage
        return { ...old, pages }
      })
      queryClient.invalidateQueries({ queryKey: ['conversations'] })
      setMessage('')
      isAtBottomRef.current = true
    },
  })

  // ── Auto-resize textarea
  function handleTextareaChange(e: React.ChangeEvent<HTMLTextAreaElement>) {
    setMessage(e.target.value)
    e.target.style.height = 'auto'
    e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px'
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      if (message.trim() && takeoverActive) sendMutation.mutate(message.trim())
    }
  }

  function handleSend() {
    if (message.trim() && takeoverActive) sendMutation.mutate(message.trim())
  }

  // ── Build date-separated message list
  const messageNodes: React.ReactNode[] = []
  let lastDateStr = ''

  for (let i = 0; i < allMessages.length; i++) {
    const msg = allMessages[i]
    const dateStr = new Date(msg.timestamp).toDateString()
    if (dateStr !== lastDateStr) {
      lastDateStr = dateStr
      messageNodes.push(
        <div key={`sep-${msg.timestamp}`} className="flex justify-center py-2">
          <span className="text-[11px] text-zinc-400 bg-zinc-100 px-3 py-1 rounded-full">
            {dateSeparatorLabel(msg.timestamp)}
          </span>
        </div>
      )
    }
    messageNodes.push(<MessageBubble key={msg.id} msg={msg} />)
  }

  return (
    <div className="flex flex-col h-full min-w-0 bg-white">
      {/* Header */}
      <div className="flex items-center gap-3 px-4 py-3.5 border-b border-zinc-100 shrink-0 bg-white z-10">
        <button
          onClick={onBack}
          className="lg:hidden p-1.5 rounded-lg text-zinc-400 hover:bg-zinc-100 transition-colors"
        >
          <ArrowLeft size={16} weight="bold" />
        </button>
        <div className="relative shrink-0">
          <Avatar name={nameValue || conv.customer_name} />
          {conv.status === 'active' && (
            <span className="absolute bottom-0 right-0 w-2.5 h-2.5 bg-emerald-400 rounded-full border-2 border-white" />
          )}
        </div>
        <div className="flex-1 min-w-0">
          {editingName ? (
            <div className="flex items-center gap-1.5">
              <input
                autoFocus
                value={nameValue}
                onChange={e => setNameValue(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter') handleRenameSubmit(); if (e.key === 'Escape') { setEditingName(false); setNameValue(conv.customer_name) } }}
                className="text-[14px] font-semibold text-[#1D1D1F] bg-zinc-50 border border-[#0ABAB5]/50 rounded-lg px-2 py-0.5 focus:outline-none w-full min-w-0"
              />
              <button onClick={handleRenameSubmit} disabled={renameMutation.isPending} className="p-1 rounded-lg text-emerald-600 hover:bg-emerald-50 disabled:opacity-50">
                {renameMutation.isPending ? <SpinnerGap size={14} className="animate-spin" /> : <Check size={14} weight="bold" />}
              </button>
              <button onClick={() => { setEditingName(false); setNameValue(conv.customer_name) }} className="p-1 rounded-lg text-zinc-400 hover:bg-zinc-100">
                <X size={14} weight="bold" />
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-1.5 group">
              <p className="text-[14px] font-semibold text-[#1D1D1F] truncate">{nameValue}</p>
              <button
                onClick={() => setEditingName(true)}
                className="p-1 rounded-lg text-zinc-300 hover:text-zinc-500 hover:bg-zinc-100 opacity-0 group-hover:opacity-100 transition-opacity"
              >
                <PencilSimple size={12} weight="bold" />
              </button>
            </div>
          )}
          <p className="text-[12px] text-zinc-400">{conv.customer_phone}</p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {takeoverActive ? (
            <button
              onClick={() => endTakeoverMutation.mutate()}
              disabled={endTakeoverMutation.isPending}
              className="text-[12px] font-semibold text-orange-600 bg-orange-50 border border-orange-100 px-3 py-1.5 rounded-xl hover:bg-orange-100 transition-colors disabled:opacity-50 active:scale-95"
            >
              {endTakeoverMutation.isPending ? <SpinnerGap size={13} className="animate-spin inline mr-1" /> : null}
              Devolver ao Bot
            </button>
          ) : (
            <button
              onClick={() => takeoverMutation.mutate()}
              disabled={takeoverMutation.isPending}
              className="text-[12px] font-semibold text-white bg-[#0ABAB5] px-3 py-1.5 rounded-xl hover:bg-[#089B97] transition-colors disabled:opacity-50 active:scale-95"
            >
              {takeoverMutation.isPending ? <SpinnerGap size={13} className="animate-spin inline mr-1" /> : null}
              Assumir
            </button>
          )}
        </div>
      </div>

      {/* Message area */}
      <div
        ref={scrollAreaRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto px-4 py-3 space-y-0.5 bg-zinc-50/30"
        style={{ overscrollBehavior: 'contain' }}
      >
        {/* Top sentinel — triggers loading older messages */}
        <div ref={topSentinelRef} className="h-1" />

        {isFetchingOlder && (
          <div className="flex justify-center py-3">
            <div className="flex items-center gap-2 text-zinc-400 text-[12px]">
              <SpinnerGap size={14} className="animate-spin" />
              Carregando mensagens anteriores...
            </div>
          </div>
        )}

        {hasOlder && !isFetchingOlder && (
          <div className="flex justify-center py-2">
            <button
              onClick={() => {
                prevScrollHeightRef.current = scrollAreaRef.current?.scrollHeight ?? 0
                fetchOlder()
              }}
              className="flex items-center gap-1.5 text-[11px] text-zinc-500 bg-white border border-zinc-200 px-3 py-1.5 rounded-full hover:border-[#0ABAB5]/50 hover:text-[#0ABAB5] transition-all"
            >
              <ArrowUp size={11} weight="bold" />
              Ver mensagens anteriores
            </button>
          </div>
        )}

        {msgsLoading ? (
          <div className="flex justify-center py-12">
            <SpinnerGap size={24} className="animate-spin text-[#0ABAB5]" />
          </div>
        ) : allMessages.length === 0 ? (
          <div className="flex flex-col items-center py-16 text-zinc-300">
            <ChatCircleDots size={36} weight="duotone" />
            <p className="text-sm mt-2 text-zinc-400">Nenhuma mensagem ainda</p>
          </div>
        ) : (
          messageNodes
        )}
      </div>

      {/* Input */}
      <div className="px-4 py-3 border-t border-zinc-100 shrink-0 bg-white">
        {takeoverActive ? (
          <div className="flex items-end gap-2">
            <div className="flex-1 bg-zinc-50 border border-zinc-200 rounded-2xl px-4 py-2.5 focus-within:border-[#0ABAB5]/50 focus-within:shadow-[0_0_0_3px_rgba(10,186,181,0.08)] transition-all">
              <textarea
                ref={textareaRef}
                value={message}
                onChange={handleTextareaChange}
                onKeyDown={handleKeyDown}
                placeholder="Digite sua mensagem... (Enter para enviar)"
                rows={1}
                className="text-[13px] bg-transparent focus:outline-none w-full resize-none placeholder:text-zinc-400 leading-relaxed"
                style={{ maxHeight: 120 }}
              />
            </div>
            <button
              onClick={handleSend}
              disabled={!message.trim() || sendMutation.isPending}
              className={`w-10 h-10 rounded-2xl text-white flex items-center justify-center transition-all active:scale-95 shrink-0 ${
                message.trim() && !sendMutation.isPending
                  ? 'bg-[#0ABAB5] hover:bg-[#089B97]'
                  : 'bg-zinc-300 cursor-not-allowed'
              }`}
            >
              {sendMutation.isPending
                ? <SpinnerGap size={14} className="animate-spin" />
                : <PaperPlaneTilt size={16} weight="bold" />
              }
            </button>
          </div>
        ) : (
          <div className="flex items-center gap-2 text-zinc-400 bg-zinc-50 rounded-2xl px-4 py-3 border border-zinc-200">
            <Robot size={15} className="text-[#0ABAB5] shrink-0" />
            <p className="text-[13px]">
              Clique em "Assumir" para responder como operador
            </p>
          </div>
        )}
        {sendMutation.isError && (
          <div className="flex items-center gap-1.5 mt-2 text-red-500 text-[12px]">
            <Warning size={13} weight="fill" />
            Falha ao enviar. Tente novamente.
          </div>
        )}
      </div>
    </div>
  )
}

// ─── Message bubble ────────────────────────────────────────────────────────────

function MessageBubble({ msg }: { msg: Message }) {
  const isUser = msg.role === 'user'
  const isOperator = msg.role === 'operator'
  const isAgent = msg.role === 'agent'

  return (
    <div className={`flex items-end gap-2 py-0.5 ${isUser ? 'justify-start' : 'justify-end'}`}>
      {isUser && (
        <div className="w-6 h-6 rounded-full bg-zinc-200 flex items-center justify-center shrink-0 mb-1">
          <User size={12} className="text-zinc-500" />
        </div>
      )}

      <div className={`max-w-[72%] rounded-2xl px-3.5 py-2.5 ${
        isUser
          ? 'bg-white border border-zinc-200 text-[#1D1D1F] rounded-bl-sm shadow-[0_1px_2px_rgba(0,0,0,0.04)]'
          : isOperator
            ? 'bg-orange-500 text-white rounded-br-sm'
            : 'bg-[#0ABAB5] text-white rounded-br-sm'
      }`}>
        {(isOperator || isAgent) && msg.operator_name && (
          <p className={`text-[10px] font-semibold mb-1 ${isOperator ? 'text-orange-100' : 'text-white/70'}`}>
            {msg.operator_name}
          </p>
        )}
        <p className="text-[13px] leading-relaxed whitespace-pre-wrap break-words">{msg.content}</p>
        <div className={`flex items-center gap-1 mt-1 ${isUser ? 'justify-start' : 'justify-end'}`}>
          {isAgent && <Robot size={9} className="text-white/60" />}
          {isOperator && <User size={9} className="text-white/60" />}
          <span className={`text-[10px] ${isUser ? 'text-zinc-400' : 'text-white/60'}`}>
            {fmtMsgTime(msg.timestamp)}
          </span>
        </div>
      </div>

      {isAgent && (
        <div className="w-6 h-6 rounded-full bg-[#0ABAB5]/15 flex items-center justify-center shrink-0 mb-1">
          <Robot size={12} className="text-[#0ABAB5]" />
        </div>
      )}
      {isOperator && (
        <div className="w-6 h-6 rounded-full bg-orange-100 flex items-center justify-center shrink-0 mb-1">
          <User size={12} className="text-orange-600" />
        </div>
      )}
    </div>
  )
}

// ─── Main Page ─────────────────────────────────────────────────────────────────

export default function ConversationsPage() {
  const queryClient = useQueryClient()
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [search, setSearch] = useState('')

  // Auto-filter by active agent — no dropdown, always show active agent's conversations
  const { data: instances = [] } = useQuery({
    queryKey: ['agent-instances'],
    queryFn: agentsApi.listInstances,
  })
  const agentId = instances.find((i: AgentInstance) => i.active)?.agent_id ?? null

  // ── WebSocket — real-time updates
  const handleWsEvent = useCallback((event: { type: string; data: any }) => {
    switch (event.type) {
      case 'new_message': {
        const chatId = event.data?.chat_id
        const msg = event.data?.message
        if (!chatId || !msg) break

        // Inject message directly into cache for instant display
        // agent_id may be included in the event or we fall back to querying all keys for this chatId
        const eventAgentId: string | undefined = event.data?.agent_id
        const updateMsgCache = (cacheKey: unknown[]) => queryClient.setQueryData(cacheKey, (old: any) => {
          if (!old?.pages?.length) return old
          const pages = [...old.pages]
          const firstPage = { ...pages[0] }
          // Avoid duplicates
          if (firstPage.items?.some((m: any) => m.id === msg.id)) return old
          const mapped = {
            id: msg.id,
            chat_id: chatId,
            role: msg.role as 'user' | 'agent' | 'operator',
            content: msg.content,
            timestamp: msg.created_at,
            operator_name: msg.sender_name,
          }
          firstPage.items = [mapped, ...(firstPage.items || [])]
          firstPage.total = (firstPage.total || 0) + 1
          pages[0] = firstPage
          return { ...old, pages }
        })
        if (eventAgentId) {
          updateMsgCache(['messages', chatId, eventAgentId])
        } else {
          // Fallback: update all message caches for this chatId
          queryClient.getQueriesData<any>({ queryKey: ['messages', chatId] })
            .forEach(([key]) => updateMsgCache(key as unknown[]))
        }
        // Optimistically update sidebar preview/time (avoids waiting for refetch)
        queryClient.setQueryData(['conversations', agentId], (old: any) => {
          if (!old?.pages) return old
          const newPages = old.pages.map((page: any) => ({
            ...page,
            items: page.items.map((c: any) =>
              c.chat_id === chatId
                ? {
                    ...c,
                    last_message_preview: msg.content?.substring(0, 100) || c.last_message_preview,
                    last_message_at: msg.created_at || c.last_message_at,
                    unread_count: (c.unread_count || 0) + (msg.role === 'user' ? 1 : 0),
                  }
                : c
            ),
          }))
          return { ...old, pages: newPages }
        })
        break
      }
      case 'new_conversation':
        queryClient.invalidateQueries({ queryKey: ['conversations'] })
        break
      case 'takeover_started':
      case 'takeover_ended':
      case 'conversation_updated':
        queryClient.invalidateQueries({ queryKey: ['conversations'] })
        break
    }
  }, [queryClient, agentId])

  useConversationsWS(handleWsEvent)

  // Subscribe to the same query the sidebar uses — needed to find selectedConv reactively
  const { data: convPages } = useInfiniteQuery({
    queryKey: ['conversations', agentId],
    queryFn: ({ pageParam = 0 }) =>
      conversationsApi.list({ offset: pageParam as number, limit: CONV_PAGE_SIZE, agent_id: agentId ?? undefined }),
    getNextPageParam: (last) => {
      const loaded = last.offset + last.items.length
      return loaded < last.total ? loaded : undefined
    },
    initialPageParam: 0,
    staleTime: 10_000,
    refetchInterval: 15_000,
  })

  const allConvs: Conversation[] = convPages?.pages.flatMap(p => p.items) ?? []
  const selectedConv = allConvs.find(c => c.chat_id === selectedId)

  return (
    <div className="flex h-[calc(100dvh-56px-64px)] lg:h-[calc(100dvh-56px)] overflow-hidden bg-white">
      {/* ── Sidebar ── */}
      <div className={`
        ${selectedId ? 'hidden lg:flex' : 'flex'}
        flex-col w-full lg:w-[320px] xl:w-[360px] shrink-0
        border-r border-zinc-100 bg-white
      `}>
        <ConversationSidebar
          selectedId={selectedId}
          onSelect={setSelectedId}
          onDeselect={() => setSelectedId(null)}
          search={search}
          onSearchChange={setSearch}
          agentId={agentId}
        />
      </div>

      {/* ── Chat area ── */}
      <div className={`
        ${selectedId ? 'flex' : 'hidden lg:flex'}
        flex-col flex-1 min-w-0
      `}>
        {selectedConv ? (
          <ChatArea
            key={selectedConv.chat_id}
            conv={selectedConv}
            onBack={() => setSelectedId(null)}
          />
        ) : (
          <div className="flex flex-1 flex-col items-center justify-center text-zinc-300 bg-zinc-50/40">
            <ChatCircleDots size={52} weight="duotone" />
            <p className="text-sm mt-3 text-zinc-400 font-medium">Selecione uma conversa</p>
            <p className="text-[12px] text-zinc-300 mt-1">As mensagens aparecem aqui</p>
          </div>
        )}
      </div>
    </div>
  )
}
