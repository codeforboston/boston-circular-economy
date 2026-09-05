import { once } from 'node:events'
import { mkdtemp, rm } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join } from 'node:path'

const temporaryDirectory = await mkdtemp(join(tmpdir(), 'circular-server-smoke-'))
process.env.DATABASE_URL = join(temporaryDirectory, 'smoke.db')
process.env.PORT = '0'

let server
let database
try {
  const databaseModule = await import('../dist/db/index.js')
  database = databaseModule.default
  const serverModule = await import('../dist/index.js')
  server = serverModule.default
  if (!server.listening) {
    await once(server, 'listening')
  }

  const address = server.address()
  if (!address || typeof address === 'string') {
    throw new Error('The smoke server did not bind a TCP port.')
  }

  const response = await fetch(`http://127.0.0.1:${address.port}/ping`)
  const result = await response.json()
  if (!response.ok || result.message !== 'pong') {
    throw new Error(`Unexpected /ping response: ${response.status}`)
  }

  console.log('Server smoke test passed.')
} finally {
  if (server?.listening) {
    await new Promise((resolve, reject) => {
      server.close((error) => (error ? reject(error) : resolve()))
    })
  }
  if (database?.open) {
    database.close()
  }
  await rm(temporaryDirectory, { recursive: true, force: true })
}
