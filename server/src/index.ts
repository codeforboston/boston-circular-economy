import express from 'express'
import './db/index.js'

const app = express()
const port = Number(process.env['PORT'] ?? 3000)

app.get('/ping', (_req, res) => {
  res.json({ message: 'pong' })
})

const server = app.listen(port, () => {
  const address = server.address()
  const boundPort = typeof address === 'object' && address ? address.port : port
  console.log(`Server running on port ${boundPort}`)
})

export default server
