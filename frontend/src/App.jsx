import { useEffect, useMemo, useState } from 'react'
import {
  QueryClient,
  QueryClientProvider,
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query'
import './App.css'
import logo from './assets/logo.png'

const API_BASE = (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '')

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Keep cached data fresh for a while so screens can render instantly
      // with cached snapshots even if the backend (BSE) is down.
      staleTime: 300_000, // 5 minutes
      // Do not automatically refetch on mount/window focus/reconnect —
      // we rely on live websocket events to refresh open screens.
      refetchOnMount: false,
      refetchOnWindowFocus: false,
      refetchOnReconnect: false,
      // Avoid long retry backoffs; show cached data instead.
      retry: 0,
      placeholderData: (previousData) => previousData,
      keepPreviousData: true,
    },
  },
})

const views = [
  { id: 'clients', label: 'Clients' },
  { id: 'trades', label: 'Trades' },
  { id: 'my-clients', label: 'My Clients' },
  { id: 'employees', label: 'Employees' },
  { id: 'incentives', label: 'Incentives' },
]

async function api(path, options) {
  // Add a short network timeout so a slow or down backend doesn't
  // delay rendering — cached data should appear immediately.
  const controller = new AbortController()
  const timeout = Number(import.meta.env.VITE_API_TIMEOUT_MS || 800)
  const timer = window.setTimeout(() => controller.abort(), timeout)

  try {
    const response = await fetch(`${API_BASE}${path}`, {
      ...options,
      signal: controller.signal,
    })

    if (!response.ok) {
      throw new Error(await response.text())
    }

    return response.json()
  } finally {
    window.clearTimeout(timer)
  }
}

function money(value) {
  return `INR ${Number(value || 0).toLocaleString('en-IN', {
    maximumFractionDigits: 2,
    minimumFractionDigits: 2,
  })}`
}

function compactDate(value) {
  if (!value) return 'Never'
  return new Date(value).toLocaleString('en-IN', {
    dateStyle: 'medium',
    timeStyle: 'short',
  })
}

function buildQuery(params) {
  const search = new URLSearchParams()

  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      search.set(key, value)
    }
  })

  const query = search.toString()
  return query ? `?${query}` : ''
}

function useLiveUpdates() {
  const queryClient = useQueryClient()
  const [connected, setConnected] = useState(false)

  useEffect(() => {
    let websocket
    let reconnectTimer
    let stopped = false

    const connect = () => {
      const wsBase = API_BASE.replace(/^http/, 'ws')
      websocket = new WebSocket(`${wsBase}/ws/live`)

      websocket.onopen = () => setConnected(true)
      websocket.onclose = () => {
        setConnected(false)
        if (!stopped) {
          reconnectTimer = window.setTimeout(connect, 2500)
        }
      }
      websocket.onerror = () => websocket.close()
      websocket.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data)
          // always refresh sync status
          queryClient.invalidateQueries({ queryKey: ['sync-status'] })

          // messages from the backend may be typed. Handle common cases:
          if (message.type === 'sync_complete') {
            // full refresh of cached datasets
            queryClient.invalidateQueries({ queryKey: ['clients'] })
            queryClient.invalidateQueries({ queryKey: ['trades'] })
            queryClient.invalidateQueries({ queryKey: ['employees'] })
            queryClient.invalidateQueries({ queryKey: ['my-clients'] })
            queryClient.invalidateQueries({ queryKey: ['incentives'] })
          } else if (message.type === 'update') {
            // payload may include which entities were updated. Prefer targeted invalidation.
            const entities = message.entities || message.keys || []
            if (entities.length > 0) {
              entities.forEach((e) => {
                // map server entity names to local query keys when necessary
                const keyMap = {
                  client: 'clients',
                  clients: 'clients',
                  trade: 'trades',
                  trades: 'trades',
                  employee: 'employees',
                  employees: 'employees',
                  incentives: 'incentives',
                }

                const q = keyMap[e] || e
                queryClient.invalidateQueries({ queryKey: [q] })
              })
            } else {
              // fallback: refresh the main datasets
              queryClient.invalidateQueries({ queryKey: ['clients'] })
              queryClient.invalidateQueries({ queryKey: ['trades'] })
              queryClient.invalidateQueries({ queryKey: ['employees'] })
              queryClient.invalidateQueries({ queryKey: ['my-clients'] })
              queryClient.invalidateQueries({ queryKey: ['incentives'] })
            }
          }
        } catch {
          queryClient.invalidateQueries()
        }
      }
    }

    connect()

    return () => {
      stopped = true
      window.clearTimeout(reconnectTimer)
      if (websocket) websocket.close()
    }
  }, [queryClient])

  return connected
}

function useEmployees() {
  return useQuery({
    queryKey: ['employees'],
    queryFn: () => api('/api/employees'),
  })
}

function Table({ columns, rows, empty = 'No rows yet.' }) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column.key}>{column.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className="empty">
                {empty}
              </td>
            </tr>
          ) : (
            rows.map((row) => (
              <tr key={row.id}>
                {columns.map((column) => (
                  <td key={column.key}>{column.render ? column.render(row) : row[column.key]}</td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  )
}

function StatusLine({ status, liveConnected }) {
  const counts = status?.cache_counts || {}

  return (
    <div className="status-line">
      <span className={`dot ${liveConnected ? 'online' : ''}`}></span>
      <span>{liveConnected ? 'Live' : 'Polling'}</span>
      <span>Status: {status?.last_status || 'Never'}</span>
      <span>Last sync: {compactDate(status?.last_sync)}</span>
      <span>
        Cache: {counts.clients || 0} clients / {counts.trades || 0} trades
      </span>
    </div>
  )
}

function ClientsView() {
  const [search, setSearch] = useState('')
  const query = useQuery({
    queryKey: ['clients', search],
    queryFn: () => api(`/api/clients${buildQuery({ search, limit: 1000 })}`),
  })

  const rows = (query.data?.data || []).map((client) => ({
    ...client,
    id: client.client_id,
  }))

  return (
    <section className="panel">
      <div className="panel-head">
        <div>
          <h1>Clients</h1>
          <p>{query.data?.total || 0} cached clients</p>
        </div>
        <label className="field compact">
          <span>Search</span>
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Name, PAN, city"
          />
        </label>
      </div>
      <Table
        columns={[
          { key: 'client_id', label: 'ID' },
          { key: 'name', label: 'Client' },
          { key: 'pan', label: 'PAN' },
          { key: 'city', label: 'City' },
          { key: 'phone', label: 'Phone' },
          { key: 'email', label: 'Email' },
        ]}
        rows={rows}
      />
    </section>
  )
}

function TradesView({ clients }) {
  const [filters, setFilters] = useState({
    client_id: '',
    start_date: '',
    end_date: '',
    stock: '',
  })
  const query = useQuery({
    queryKey: ['trades', filters],
    queryFn: () => api(`/api/trades${buildQuery({ ...filters, limit: 500 })}`),
  })

  const rows = (query.data?.data || []).map((trade) => ({
    ...trade,
    id: trade.trade_id,
  }))

  return (
    <section className="panel">
      <div className="panel-head stacked">
        <div>
          <h1>Trades</h1>
          <p>{query.data?.total || 0} matching cached trades</p>
        </div>
        <div className="filters">
          <label className="field">
            <span>Client</span>
            <select
              value={filters.client_id}
              onChange={(event) => setFilters({ ...filters, client_id: event.target.value })}
            >
              <option value="">All clients</option>
              {clients.map((client) => (
                <option key={client.client_id} value={client.client_id}>
                  {client.client_id} - {client.name}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>From</span>
            <input
              type="date"
              value={filters.start_date}
              onChange={(event) => setFilters({ ...filters, start_date: event.target.value })}
            />
          </label>
          <label className="field">
            <span>To</span>
            <input
              type="date"
              value={filters.end_date}
              onChange={(event) => setFilters({ ...filters, end_date: event.target.value })}
            />
          </label>
          <label className="field">
            <span>Stock</span>
            <input
              value={filters.stock}
              onChange={(event) => setFilters({ ...filters, stock: event.target.value })}
              placeholder="TCS"
            />
          </label>
        </div>
      </div>
      <Table
        columns={[
          { key: 'trade_id', label: 'Trade' },
          { key: 'trade_date', label: 'Date' },
          { key: 'client_name', label: 'Client' },
          { key: 'stock', label: 'Stock' },
          { key: 'quantity', label: 'Qty' },
          { key: 'brokerage', label: 'Brokerage', render: (row) => money(row.brokerage) },
        ]}
        rows={rows}
      />
    </section>
  )
}

function MyClientsView({ employeeId }) {
  const query = useQuery({
    queryKey: ['my-clients', employeeId],
    queryFn: () => api(`/api/my-clients${buildQuery({ employee_id: employeeId })}`),
    enabled: Boolean(employeeId),
  })
  const rows = (query.data?.data || []).map((client) => ({
    ...client,
    id: client.client_id,
  }))

  return (
    <section className="panel">
      <div className="panel-head">
        <div>
          <h1>My Clients</h1>
          <p>{query.data?.total || 0} mapped clients</p>
        </div>
      </div>
      <Table
        columns={[
          { key: 'client_id', label: 'ID' },
          { key: 'name', label: 'Client' },
          { key: 'city', label: 'City' },
          { key: 'trade_count', label: 'Trades' },
          { key: 'brokerage', label: 'Brokerage', render: (row) => money(row.brokerage) },
          { key: 'email', label: 'Email' },
        ]}
        rows={rows}
      />
    </section>
  )
}

function EmployeesView({ employees }) {
  const rows = employees.map((employee) => ({
    ...employee,
    id: employee.employee_id,
  }))

  return (
    <section className="panel">
      <div className="panel-head">
        <div>
          <h1>Employees</h1>
          <p>{employees.length} employees on platform</p>
        </div>
      </div>
      <Table
        columns={[
          { key: 'employee_id', label: 'ID' },
          { key: 'name', label: 'Employee' },
          { key: 'department', label: 'Department' },
          { key: 'client_count', label: 'Clients' },
          { key: 'brokerage', label: 'Brokerage', render: (row) => money(row.brokerage) },
          { key: 'incentive', label: 'Incentive', render: (row) => money(row.incentive) },
        ]}
        rows={rows}
      />
    </section>
  )
}

function IncentivesView({ role, employeeId }) {
  const query = useQuery({
    queryKey: ['incentives', role, employeeId],
    queryFn: () => api(`/api/incentives${buildQuery({ role, employee_id: employeeId })}`),
    enabled: role === 'management' || Boolean(employeeId),
  })

  const rows = (query.data?.data || []).map((employee) => ({
    ...employee,
    id: employee.employee_id,
  }))
  const totalIncentive = rows.reduce((sum, row) => sum + Number(row.incentive || 0), 0)

  return (
    <section className="panel">
      <div className="panel-head">
        <div>
          <h1>Incentives</h1>
          <p>{money(totalIncentive)} payable in this cached snapshot</p>
        </div>
      </div>
      <Table
        columns={[
          { key: 'employee_id', label: 'ID' },
          { key: 'name', label: 'Employee' },
          { key: 'client_count', label: 'Clients' },
          { key: 'brokerage', label: 'Brokerage', render: (row) => money(row.brokerage) },
          { key: 'incentive', label: 'Incentive', render: (row) => money(row.incentive) },
        ]}
        rows={rows}
      />
    </section>
  )
}

function Portal() {
  const [activeView, setActiveView] = useState('clients')
  const [role, setRole] = useState('management')
  const [employeeId, setEmployeeId] = useState('')
  const liveConnected = useLiveUpdates()
  const employeesQuery = useEmployees()
  const statusQuery = useQuery({
    queryKey: ['sync-status'],
    queryFn: () => api('/api/sync/status'),
    refetchInterval: 5000,
  })
  const clientsQuery = useQuery({
    queryKey: ['clients', 'options'],
    queryFn: () => api('/api/clients?limit=1000'),
  })
  const syncMutation = useMutation({
    mutationFn: () => api('/api/sync/run', { method: 'POST' }),
    onSettled: () => queryClient.invalidateQueries({ queryKey: ['sync-status'] }),
  })

  const employees = useMemo(
    () => employeesQuery.data?.data || [],
    [employeesQuery.data],
  )
  const clients = useMemo(
    () => clientsQuery.data?.data || [],
    [clientsQuery.data],
  )
  const effectiveEmployeeId = employeeId || String(employees[0]?.employee_id || '')

  const selectedEmployee = useMemo(
    () => employees.find((employee) => String(employee.employee_id) === effectiveEmployeeId),
    [effectiveEmployeeId, employees],
  )

  const content = {
    clients: <ClientsView />,
    trades: <TradesView clients={clients} />,
    'my-clients': <MyClientsView employeeId={effectiveEmployeeId} />,
    employees: <EmployeesView employees={employees} />,
    incentives: <IncentivesView role={role} employeeId={effectiveEmployeeId} />,
  }[activeView]

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <img src={logo} alt="Arham logo" className="brand-mark" />
          <div>
            <strong>Arham Ops</strong>
            <span>Incentive Portal</span>
          </div>
        </div>
        <nav>
          {views.map((view) => (
            <button
              key={view.id}
              className={activeView === view.id ? 'active' : ''}
              type="button"
              onClick={() => setActiveView(view.id)}
            >
              {view.label}
            </button>
          ))}
        </nav>
      </aside>

      <main className="workspace">
        <header className="topbar">
          <div className="identity">
            <label className="field inline">
              <span>Role</span>
              <select value={role} onChange={(event) => setRole(event.target.value)}>
                <option value="management">Management</option>
                <option value="employee">Employee</option>
              </select>
            </label>
            <label className="field inline employee-picker">
              <span>Employee</span>
              <select
                value={effectiveEmployeeId}
                onChange={(event) => setEmployeeId(event.target.value)}
              >
                {employees.map((employee) => (
                  <option key={employee.employee_id} value={employee.employee_id}>
                    {employee.name}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <button
            className="sync-button"
            type="button"
            disabled={statusQuery.data?.sync_running || syncMutation.isPending}
            onClick={() => syncMutation.mutate()}
          >
            {statusQuery.data?.sync_running ? 'Syncing' : 'Sync Now'}
          </button>
        </header>

        <StatusLine status={statusQuery.data} liveConnected={liveConnected} />

        {statusQuery.data?.last_error ? (
          <div className="notice">
            BSE refresh failed; cached screens are still being served. {statusQuery.data.last_error}
          </div>
        ) : null}

        {selectedEmployee && role === 'employee' ? (
          <div className="context-line">
            Acting as {selectedEmployee.name} ({selectedEmployee.email})
          </div>
        ) : null}

        {content}
      </main>
    </div>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Portal />
    </QueryClientProvider>
  )
}
