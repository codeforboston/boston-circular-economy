import { useState } from 'react'
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/decide/service-type/')({
  component: ServiceTypePage,
})

const SERVICE_TYPES = [
  {
    value: 'repair',
    title: 'Repair',
    description: 'Fix your item or learn skills? Find service providers.',
  },
  {
    value: 'reuse',
    title: 'Reuse',
    description: 'Get, buy, or donate items? Find nearby locations.',
  },
] as const

type ServiceType = (typeof SERVICE_TYPES)[number]['value']

function ServiceTypePage() {
  const [serviceType, setServiceType] = useState<ServiceType | null>(null)

  return (
    <main>
      <h1>Service type</h1>
      <YouChoose value={serviceType} onChange={setServiceType} />
    </main>
  )
}

type YouChooseProps = {
  value: ServiceType | null
  onChange: (value: ServiceType) => void
}

function YouChoose({ value, onChange }: YouChooseProps) {
  return (
    <section aria-labelledby="you-choose-heading">
      <h2 id="you-choose-heading">You choose</h2>
      <fieldset style={{ border: 'none', padding: 0, margin: 0 }}>
        <legend>
          Select the service type if you know what you want to do with your item(s).
        </legend>
        {SERVICE_TYPES.map(({ value: optionValue, title, description }) => (
          <label
            key={optionValue}
            style={{
              display: 'block',
              border: '1px solid #ccc',
              padding: '1rem',
              marginTop : '1rem',
            }}
          >
            <input
              type="radio"
              name="service-type"
              value={optionValue}
              checked={value === optionValue}
              onChange={() => onChange(optionValue)}
            />{' '}
            <strong>{title}</strong>
            <span style={{ display: 'block' }}>{description}</span>
          </label>
        ))}
      </fieldset>
    </section>
  )
}
