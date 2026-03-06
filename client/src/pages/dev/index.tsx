import { createFileRoute, Link } from '@tanstack/react-router'

export const Route = createFileRoute('/dev/')({
  component: DevIndex,
})

const modules = import.meta.glob('./**/index.tsx')

type TreeNode = {
  hasRoute: boolean
  children: Record<string, TreeNode>
}

function buildTree(paths: string[]): Record<string, TreeNode> {
  const root: Record<string, TreeNode> = {}

  for (const path of paths) {
    const parts = path
      .replace(/^\.\//, '')
      .replace(/\/index\.tsx$/, '')
      .split('/')

    let level = root
    for (const part of parts) {
      level[part] ??= { hasRoute: false, children: {} }
      level = level[part].children
    }

    // Mark the node at this path as having a route
    let node = root
    for (let i = 0; i < parts.length - 1; i++) {
      node = node[parts[i]].children
    }
    node[parts[parts.length - 1]].hasRoute = true
  }

  return root
}

function TreeList({
  nodes,
  prefix,
}: {
  nodes: Record<string, TreeNode>
  prefix: string
}) {
  const entries = Object.entries(nodes)
  if (entries.length === 0) return null

  return (
    <ul style={{ paddingLeft: '1.25rem', margin: '0.25rem 0' }}>
      {entries.map(([key, node]) => {
        const route = `${prefix}${key}/`
        return (
          <li key={key}>
            {node.hasRoute ? (
              <Link to={route as '/dev'}>{key}</Link>
            ) : (
              <span>{key}</span>
            )}
            <TreeList nodes={node.children} prefix={route} />
          </li>
        )
      })}
    </ul>
  )
}

function DevIndex() {
  const paths = Object.keys(modules)
  const tree = buildTree(paths)

  return (
    <main>
      <style>{`
        .dev-index a:link { color: #5aacff; }
        .dev-index a:visited { color: #c084fc; }
      `}</style>
      <h1>Dev Prototypes</h1>
      <div style={{ display: 'flex', justifyContent: 'center' }}>
        <div className="dev-index" style={{ textAlign: 'left' }}>
          <TreeList nodes={tree} prefix="/dev/" />
        </div>
      </div>
    </main>
  )
}
