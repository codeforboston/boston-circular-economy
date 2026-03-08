import { createFileRoute, Link } from '@tanstack/react-router'

export const Route = createFileRoute('/dev/')({
  component: DevIndex,
})

const folderModules = import.meta.glob('./*/index.tsx')
const fileModules = import.meta.glob('./*.tsx', { eager: false })

function DevIndex() {
  const fromFolders = Object.keys(folderModules).map((path) =>
    path.replace(/^\.\//, '').replace(/\/index\.tsx$/, ''),
  )
  const fromFiles = Object.keys(fileModules)
    .map((path) => path.replace(/^\.\//, '').replace(/\.tsx$/, ''))
    .filter((name) => name !== 'index')

  const prototypes = [...fromFiles, ...fromFolders].sort()

  return (
    <main>
      <h1>Dev Prototypes</h1>
      <div style={{ display: 'flex', justifyContent: 'center' }}>
        <div className="dev-index" style={{ textAlign: 'left' }}>
          <ul style={{ paddingLeft: '1.25rem', margin: '0.25rem 0' }}>
            {prototypes.map((name) => (
              <li key={name}>
                <Link to={`/dev/${name}/` as '/dev'}>{name}</Link>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </main>
  )
}
