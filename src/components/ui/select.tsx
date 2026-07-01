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

interface SelectItemEntry {
  value: string
  label: React.ReactNode
}

const SelectContext = React.createContext<{
  value: string
  onValueChange: (value: string) => void
  items: SelectItemEntry[]
  registerItem: (item: SelectItemEntry) => () => void
}>({
  value: "",
  onValueChange: () => {},
  items: [],
  registerItem: () => () => {},
})

export function Select({ value, onValueChange, children }: SelectProps) {
  const [items, setItems] = React.useState<SelectItemEntry[]>([])

  const registerItem = React.useCallback((item: SelectItemEntry) => {
    setItems(prev => [...prev, item])
    return () => {
      setItems(prev => prev.filter(i => i.value !== item.value))
    }
  }, [])

  return (
    <SelectContext.Provider value={{ value, onValueChange, items, registerItem }}>
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
        "flex h-10 w-full rounded-md border border-input bg-background text-foreground px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
        className
      )}
    >
      {context.items.map(item => (
        <option key={item.value} value={item.value}>{item.label}</option>
      ))}
    </select>
  )
}

export function SelectValue() {
  const context = React.useContext(SelectContext)
  return <>{context.value}</>
}

export function SelectContent({ children }: SelectContentProps) {
  return <>{children}</>
}

export function SelectItem({ value, children }: SelectItemProps) {
  const context = React.useContext(SelectContext)

  React.useEffect(() => {
    const unregister = context.registerItem({ value, label: children })
    return unregister
  }, [value, children])

  return null
}
