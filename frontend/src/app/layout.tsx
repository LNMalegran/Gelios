import type { Metadata } from 'next';
import './globals.css'; // Импорт базовых стилей Tailwind

export const metadata: Metadata = {
  title: 'Протокол «ГЕЛИОС»',
  description: 'Система управления КПК Омской Зоны',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ru">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
