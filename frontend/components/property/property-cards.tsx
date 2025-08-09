'use client'

interface PropertyItem {
  address: string
  price?: string
  beds?: string
  baths?: string
  type?: string
}

function parsePropertyText(text: string): PropertyItem[] | null {
  if (!/properties matching your criteria:/i.test(text)) return null
  const lines = text.split('\n')
  const items: PropertyItem[] = []
  let current: Partial<PropertyItem> | null = null
  for (const raw of lines) {
    const line = raw.trim()
    const mIdx = line.match(/^\d+\.\s+(.*)$/)
    if (mIdx) {
      if (current) items.push(current as PropertyItem)
      current = { address: mIdx[1] }
      continue
    }
    if (!current) continue
    const mPrice = line.match(/^Price:\s*(.*)$/i)
    if (mPrice) { current.price = mPrice[1]; continue }
    const mBedBath = line.match(/^(\d+)\s*bed.*?(\d+)\s*bath/i)
    if (mBedBath) { current.beds = mBedBath[1]; current.baths = mBedBath[2]; continue }
    const mType = line.match(/^Type:\s*(.*)$/i)
    if (mType) { current.type = mType[1]; continue }
  }
  if (current) items.push(current as PropertyItem)
  return items.length ? items : null
}

export function PropertyCardsFromText({ text }: { text: string }) {
  const items = parsePropertyText(text)
  if (!items) return null
  return (
    <div className="mt-2 grid gap-3 sm:grid-cols-2">
      {items.map((p, i) => (
        <div key={`${p.address}-${i}`} className="rounded-lg border bg-white/70 dark:bg-white/5 dark:border-white/10 p-3">
          <div className="text-sm font-medium dark:text-white">{p.address}</div>
          {p.price && <div className="text-xs text-text-secondary dark:text-white/70">{p.price}</div>}
          <div className="mt-1 text-xs text-text-secondary dark:text-white/70">
            {p.beds ? `${p.beds} bed` : ''}{p.baths ? `, ${p.baths} bath` : ''}{p.type ? ` • ${p.type}` : ''}
          </div>
        </div>
      ))}
    </div>
  )
}


