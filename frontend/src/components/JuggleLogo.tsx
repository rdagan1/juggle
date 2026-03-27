interface JuggleLogoProps {
  size?: number;
}

export function JuggleLogo({ size = 28 }: JuggleLogoProps) {
  const cx = size / 2;
  const cy = size / 2;
  const R = size * 0.34; // circumradius
  const r = size * 0.13; // dot radius

  // Equilateral triangle vertices: top, bottom-right, bottom-left
  const v = [-90, 30, 150].map((deg) => {
    const rad = (deg * Math.PI) / 180;
    return { x: cx + R * Math.cos(rad), y: cy + R * Math.sin(rad) };
  });

  return (
    <svg
      width={size}
      height={size}
      viewBox={`0 0 ${size} ${size}`}
      fill="none"
      aria-hidden="true"
    >
      {v.map((p, i) => (
        <circle key={i} cx={p.x} cy={p.y} r={r} fill="white" />
      ))}
    </svg>
  );
}
