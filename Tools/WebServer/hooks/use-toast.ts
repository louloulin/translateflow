import { useState, useEffect } from "react"

export type ToastProps = {
  title?: string
  description?: string
  variant?: "default" | "destructive"
}

export const useToast = () => {
  const [toasts, setToasts] = useState<ToastProps[]>([])

  const toast = ({ title, description, variant }: ToastProps) => {
    const newToast = { title, description, variant }
    setToasts((prev) => [...prev, newToast])
    
    // In a real implementation, this would trigger a UI component.
    // For now, we just log to console to simulate the toast.
    console.log(`[Toast] ${title}: ${description} (${variant})`)
    
    // Simulate auto-dismiss
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t !== newToast))
    }, 3000)
  }

  return {
    toast,
    toasts,
    dismiss: (toastId?: string) => {}
  }
}