import type { Metadata } from 'next'
import './globals.css'
import { ThemeToggle } from '@/components/theme-toggle'

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
    <html lang="en" suppressHydrationWarning>
      <body
        suppressHydrationWarning
        className="font-sans antialiased bg-white text-text-primary dark:bg-[#0B0C0E] dark:text-white transition-colors duration-300"
      >
        <div className="fixed top-4 right-4 z-50">
          <ThemeToggle />
        </div>
        {children}
      </body>
    </html>
  )
}