import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'ReAgent - Sydney Real Estate Intelligence',
  description: 'Professional real estate intelligence platform for Sydney',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body 
        className="font-sans antialiased bg-white text-text-primary"
        suppressHydrationWarning={true}
      >
        {children}
      </body>
    </html>
  )
}