import express from 'express'
import db from './db/index.ts'

const app = express()
const port = process.env['PORT'] ?? 3000

app.get('/ping', (_req, res) => {
  res.json({ message: 'pong' })
})

app.listen(port, () => {
  console.log(`Server running on port ${port}`)
})
