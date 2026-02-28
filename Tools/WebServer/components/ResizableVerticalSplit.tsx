import React, { useEffect, useMemo, useRef, useState } from 'react'
import { GripHorizontal } from 'lucide-react'
import { cn } from '@/lib/utils'

type DragState = {
  pointerId: number
  startY: number
  startTopPx: number
}

export interface ResizableVerticalSplitProps {
  ratio: number
  onRatioCommit: (ratio: number) => void
  minTopPx?: number
  minBottomPx?: number
  top: React.ReactNode
  bottom: React.ReactNode
  className?: string
}

/**
 * Renders a vertical split layout with a draggable horizontal handle.
 */
export const ResizableVerticalSplit: React.FC<ResizableVerticalSplitProps> = ({
  ratio,
  onRatioCommit,
  minTopPx = 220,
  minBottomPx = 260,
  top,
  bottom,
  className,
}) => {
  const containerRef = useRef<HTMLDivElement>(null)
  const [containerHeight, setContainerHeight] = useState(0)
  const [topPx, setTopPx] = useState<number | null>(null)
  const dragRef = useRef<DragState | null>(null)
  const dividerPx = 10

  const clampTopPx = useMemo(() => {
    return (px: number, h: number) => {
      const maxTop = Math.max(minTopPx, h - minBottomPx - dividerPx)
      const clamped = Math.min(maxTop, Math.max(minTopPx, px))
      return Math.round(clamped)
    }
  }, [minBottomPx, minTopPx])

  useEffect(() => {
    const el = containerRef.current
    if (!el) return

    const ro = new ResizeObserver(entries => {
      const next = entries[0]?.contentRect?.height
      if (typeof next === 'number') setContainerHeight(Math.floor(next))
    })
    ro.observe(el)
    return () => ro.disconnect()
  }, [])

  useEffect(() => {
    if (!containerHeight) return
    if (dragRef.current) return
    setTopPx(clampTopPx(containerHeight * ratio, containerHeight))
  }, [clampTopPx, containerHeight, ratio])

  useEffect(() => {
    const onMove = (e: PointerEvent) => {
      const drag = dragRef.current
      const el = containerRef.current
      if (!drag || !el) return
      if (e.pointerId !== drag.pointerId) return
      const h = el.clientHeight
      const delta = e.clientY - drag.startY
      const nextTop = clampTopPx(drag.startTopPx + delta, h)
      setTopPx(nextTop)
    }

    const onUp = (e: PointerEvent) => {
      const drag = dragRef.current
      const el = containerRef.current
      if (!drag || !el) return
      if (e.pointerId !== drag.pointerId) return
      dragRef.current = null
      try {
        el.releasePointerCapture(e.pointerId)
      } catch {
        // ignore
      }
      const h = el.clientHeight
      const finalTop = typeof topPx === 'number' ? topPx : clampTopPx(h * ratio, h)
      const nextRatio = h > 0 ? finalTop / h : ratio
      onRatioCommit(Math.min(0.8, Math.max(0.2, nextRatio)))
    }

    window.addEventListener('pointermove', onMove)
    window.addEventListener('pointerup', onUp)
    window.addEventListener('pointercancel', onUp)
    return () => {
      window.removeEventListener('pointermove', onMove)
      window.removeEventListener('pointerup', onUp)
      window.removeEventListener('pointercancel', onUp)
    }
  }, [clampTopPx, onRatioCommit, ratio, topPx])

  const handlePointerDown = (e: React.PointerEvent) => {
    const el = containerRef.current
    if (!el) return
    const h = el.clientHeight
    const currentTop = typeof topPx === 'number' ? topPx : clampTopPx(h * ratio, h)
    dragRef.current = {
      pointerId: e.pointerId,
      startY: e.clientY,
      startTopPx: currentTop,
    }
    try {
      el.setPointerCapture(e.pointerId)
    } catch {
      return
    }
  }

  const computedTopPx = typeof topPx === 'number'
    ? topPx
    : (containerHeight ? clampTopPx(containerHeight * ratio, containerHeight) : null)

  return (
    <div ref={containerRef} className={cn('flex-1 min-h-0 flex flex-col', className)}>
      <div style={computedTopPx ? { height: computedTopPx } : undefined} className="min-h-0 overflow-hidden">
        {top}
      </div>

      <div
        className="h-[10px] flex items-center justify-center cursor-row-resize select-none"
        onPointerDown={handlePointerDown}
        role="separator"
        aria-orientation="horizontal"
      >
        <div className="h-[6px] w-full rounded-full bg-slate-800/60 hover:bg-slate-700/70 transition-colors flex items-center justify-center">
          <GripHorizontal size={14} className="text-slate-500" />
        </div>
      </div>

      <div style={minBottomPx ? { minHeight: minBottomPx } : undefined} className="flex-1 min-h-0 overflow-hidden">
        {bottom}
      </div>
    </div>
  )
}
