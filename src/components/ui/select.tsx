import * as React from "react"
import { cn } from "@/lib/utils"

interface SelectProps {
  value: string
  onValueChange: (value: string) => void
  children: React.ReactNode
}

interface SelectTriggerProps {
  children: React.ReactNode
  className?: string
}

interface SelectContentProps {
  children: React.ReactNode
  className?: string
}

interface SelectItemProps {
  value: string
  children: React.ReactNode
}

const SelectContext = React.createContext<{
  value: string
  onValueChange: (value: string) => void
}>({ value: "", onValueChange: () => {} })

export function Select({ value, onValueChange, children }: SelectProps) {
  return (
    <SelectContext.Provider value={{ value, onValueChange }}>
      {children}
    </SelectContext.Provider>
  )
}

export function SelectTrigger({ children, className }: SelectTriggerProps) {
  const context = React.useContext(SelectContext)
  return (
    <select
      value={context.value}
      onChange={(e) => context.onValueChange(e.target.value)}
      className={cn(
        "flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
        className
      )}
    >
      {children}
    </select>
  )
}

export function SelectValue() {
  const context = React.useContext(SelectContext)
  return <>{context.value}</>
}

export function SelectContent({ children, className }: SelectContentProps) {
  return <>{children}</>
}

export function SelectItem({ value, children }: SelectItemProps) {
  return <option value={value}>{children}</option>
}
