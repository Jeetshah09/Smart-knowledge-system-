import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "./providers";
import { Toaster } from "@/components/ui";

export const metadata: Metadata = {
  title: "AI Smart Knowledge Management System",
  description:
    "Upload your learning resources, ask questions, understand complex topics and turn information into interactive knowledge.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <Providers>{children}</Providers>
        <Toaster />
      </body>
    </html>
  );
}
