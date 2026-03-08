import { createFileRoute, Link } from '@tanstack/react-router'

export const Route = createFileRoute('/dev/')({
  component: DevIndex,
})

const modules = import.meta.glob('./*/index.tsx')

function DevIndex() {
  const prototypes = Object.keys(modules).map((path) =>
    path.replace(/^\.\//, '').replace(/\/index\.tsx$/, ''),
  )

  return (
    <main>
      <style>{`
        .dev-index a:link { color: #5aacff; }
        .dev-index a:visited { color: #c084fc; }
      `}</style>
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
