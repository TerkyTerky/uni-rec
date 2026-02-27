import { useState } from "react"
import { Star } from "lucide-react"
import { cn } from "@/lib/utils"

type Props = {
  value?: number
  onChange: (value: number) => void
  disabled?: boolean
}

export default function StarRating({ value = 0, onChange, disabled = false }: Props) {
  const [hoverValue, setHoverValue] = useState(0)

  return (
    <div className="flex gap-1" onMouseLeave={() => setHoverValue(0)}>
      {[1, 2, 3, 4, 5].map((rating) => (
        <button
          key={rating}
          type="button"
          disabled={disabled}
          onClick={() => onChange(rating)}
          onMouseEnter={() => !disabled && setHoverValue(rating)}
          className={cn(
            "transition-colors focus:outline-none focus:ring-2 focus:ring-primary/20 rounded-sm p-0.5",
            disabled ? "cursor-not-allowed opacity-50" : "cursor-pointer hover:scale-110"
          )}
        >
          <Star
            className={cn(
              "h-5 w-5 transition-all",
              (hoverValue || value) >= rating
                ? "fill-yellow-400 text-yellow-400"
                : "text-slate-300 fill-transparent"
            )}
          />
        </button>
      ))}
    </div>
  )
}
