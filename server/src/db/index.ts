import Database from 'better-sqlite3'

const db = new Database(process.env['DATABASE_URL'] ?? 'dev.db')
db.pragma('journal_mode = WAL')

export default db
