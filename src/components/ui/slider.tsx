import * as React from "react"
import { cn } from "@/lib/utils"

interface SliderProps {
  value: number
  min: number
  max: number
  step: number
  onValueChange: (value: number) => void
  className?: string
}

export function Slider({ value, min, max, step, onValueChange, className }: SliderProps) {
  return (
    <input
      type="range"
      min={min}
      max={max}
      step={step}
      value={value}
      onChange={(e) => onValueChange(parseFloat(e.target.value))}
      className={cn(
        "w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700",
        className
      )}
    />
  )
}
