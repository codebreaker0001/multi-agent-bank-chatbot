const VARIANTS = {
  primary:
    "bg-navy-900 text-white hover:bg-navy-800 focus-visible:ring-navy-900 disabled:bg-navy-400",
  accent:
    "bg-accent-500 text-white hover:bg-accent-600 focus-visible:ring-accent-500 disabled:bg-accent-100",
  secondary:
    "bg-white text-navy-800 border border-navy-100 hover:bg-navy-50 focus-visible:ring-navy-400",
  ghost:
    "bg-transparent text-navy-600 hover:bg-navy-50 focus-visible:ring-navy-400",
  destructive:
    "bg-negative text-white hover:bg-negative/90 focus-visible:ring-negative disabled:bg-negative/40",
};

const SIZES = {
  sm: "h-8 px-3 text-[13px] gap-1.5",
  md: "h-10 px-4 text-sm gap-2",
  lg: "h-12 px-6 text-[15px] gap-2",
};

export default function Button({
  variant = "primary",
  size = "md",
  className = "",
  children,
  ...props
}) {
  return (
    <button
      className={`inline-flex items-center justify-center rounded-xl font-semibold
        transition-colors duration-150 focus-visible:outline-none focus-visible:ring-2
        focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60
        ${VARIANTS[variant]} ${SIZES[size]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}
