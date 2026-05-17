import * as React from "react"
import { cn } from "@/lib/utils"

interface TabsProps {
  defaultValue: string
  children: React.ReactNode
  className?: string
}

interface TabsListProps {
  children: React.ReactNode
  className?: string
}

interface TabsTriggerProps {
  value: string
  children: React.ReactNode
  className?: string
}

interface TabsContentProps {
  value: string
  children: React.ReactNode
  className?: string
}

const TabsContext = React.createContext<{
  value: string
  setValue: (value: string) => void
}>({ value: "", setValue: () => {} })

export function Tabs({ defaultValue, children, className }: TabsProps) {
  const [value, setValue] = React.useState(defaultValue)
  return (
    <TabsContext.Provider value={{ value, setValue }}>
      <div className={className}>{children}</div>
    </TabsContext.Provider>
  )
}

export function TabsList({ children, className }: TabsListProps) {
  return <div className={cn("flex", className)}>{children}</div>
}

export function TabsTrigger({ value, children, className }: TabsTriggerProps) {
  const context = React.useContext(TabsContext)
  return (
    <button
      className={cn(
        "px-3 py-1.5 text-sm font-medium transition-all",
        context.value === value
          ? "bg-background shadow-sm"
          : "hover:bg-muted",
        className
      )}
      onClick={() => context.setValue(value)}
    >
      {children}
    </button>
  )
}

export function TabsContent({ value, children, className }: TabsContentProps) {
  const context = React.useContext(TabsContext)
  if (context.value !== value) return null
  return <div className={className}>{children}</div>
}
