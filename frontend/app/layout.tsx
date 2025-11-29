import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'The North Jersey Project',
  description: 'Chat with Tony Soprano - A fine-tuned AI chatbot',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
