import { useEffect, useRef, useState } from "react";

interface MenuItem {
  label: string;
  onClick: () => void;
  danger?: boolean;
}

interface ThreeDotMenuProps {
  items: MenuItem[];
}

export function ThreeDotMenu({ items }: ThreeDotMenuProps) {
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open]);

  return (
    <div ref={containerRef} className="relative" dir="rtl">
      <button
        onClick={(e) => {
          e.stopPropagation();
          setOpen((v) => !v);
        }}
        className="w-7 h-7 flex items-center justify-center rounded-full text-slate-400 hover:bg-navy-50 hover:text-slate-600 transition-colors"
        aria-label="תפריט"
        aria-haspopup="true"
        aria-expanded={open}
      >
        ⋮
      </button>

      {open && (
        <div
          className="absolute left-0 top-8 z-50 min-w-[110px] bg-white rounded-xl border border-navy-100 shadow-lg py-1"
          role="menu"
        >
          {items.map((item) => (
            <button
              key={item.label}
              role="menuitem"
              onClick={(e) => {
                e.stopPropagation();
                setOpen(false);
                item.onClick();
              }}
              className={`w-full text-right px-4 py-2 text-sm transition-colors hover:bg-navy-50 ${
                item.danger ? "text-red-600 hover:text-red-700" : "text-gray-700"
              }`}
            >
              {item.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
