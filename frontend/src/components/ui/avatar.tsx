import { cn } from "@/lib/utils";

type AvatarProps = {
  name?: string;
  src?: string | null;
  className?: string;
};

function initials(name: string) {
  return name
    .split(" ")
    .map((part) => part[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
}

export function Avatar({ name = "User", src, className }: AvatarProps) {
  if (src) {
    return (
      <img
        src={src}
        alt={name}
        className={cn("h-8 w-8 rounded-full object-cover ring-2 ring-border", className)}
      />
    );
  }

  return (
    <div
      className={cn(
        "flex h-8 w-8 items-center justify-center rounded-full bg-primary text-xs font-semibold text-primary-foreground ring-2 ring-border",
        className,
      )}
      aria-hidden
    >
      {initials(name)}
    </div>
  );
}
