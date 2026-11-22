import { useState } from 'react'
import { createFileRoute } from '@tanstack/react-router'

export const MAX_INPUT_LENGTH = 100

export const Route = createFileRoute('/decide/')({
  component: DecidePage,
})

function DecidePage() {
    const [itemInput, setItemInput] = useState('')

  return (
    <main>
      <h1>Circular Economy Decision Tool</h1>
      <HelpYouDecide value={itemInput   } onChange={setItemInput} />
    </main>
  )
}
type HelpYouDecideProps = {
    value: string
    onChange: (value: string) => void
}

function HelpYouDecide({ value, onChange }: HelpYouDecideProps) {
    return (
        <section
        aria-labelledby="help-you-decide-heading"
        style={{ background: '#f1f1f1', padding: '1rem'}}
        >
            <h2 id="help-you-decide-heading">Help you decide</h2>
            <label htmlFor="item-input">What is your item?</label>
            <input
                id="item-input"
                type="text"
                placeholder="Clothing"
                maxLength={MAX_INPUT_LENGTH}
                value={value}
                onChange={(e) => onChange(e.target.value)}
                style={{ display: 'block', width: '100%', marginTop: '0.5rem' }}
            />
        </section>
    )
}