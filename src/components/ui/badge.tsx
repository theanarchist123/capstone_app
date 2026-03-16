import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 border",
  {
    variants: {
      variant: {
        default: "bg-primary/15 text-primary border-primary/30",
        secondary: "bg-secondary text-secondary-foreground border-border",
        destructive: "bg-destructive/15 text-destructive border-destructive/30",
        outline: "border-border text-foreground",
        teal: "bg-[#0891B2]/15 text-[#0891B2] border-[#0891B2]/30",
        success: "bg-emerald-500/15 text-emerald-500 border-emerald-500/30 dark:text-emerald-400",
        warning: "bg-amber-500/15 text-amber-600 border-amber-500/30 dark:text-amber-400",
        danger: "bg-rose-500/15 text-rose-600 border-rose-500/30 dark:text-rose-400",
        purple: "bg-purple-500/15 text-purple-600 border-purple-500/30 dark:text-purple-400",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  )
}

export { Badge, badgeVariants }
