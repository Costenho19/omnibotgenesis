import { motion } from 'framer-motion';

interface OmnixLogoProps {
  size?: string | number;
  opacity?: number;
  animate?: boolean;
  glow?: boolean;
  className?: string;
  style?: React.CSSProperties;
}

export function OmnixLogo({
  size = '8vw',
  opacity = 1,
  animate = false,
  glow = false,
  className,
  style,
}: OmnixLogoProps) {
  return (
    <motion.div
      className={className}
      style={{
        width: size,
        height: size,
        position: 'relative',
        flexShrink: 0,
        ...style,
      }}
      animate={animate ? { rotate: [0, 360] } : undefined}
      transition={animate ? { duration: 18, repeat: Infinity, ease: 'linear' } : undefined}
    >
      {glow && (
        <div
          style={{
            position: 'absolute',
            inset: '-30%',
            borderRadius: '50%',
            background: 'radial-gradient(circle, rgba(212,168,67,0.18) 0%, transparent 70%)',
            pointerEvents: 'none',
          }}
        />
      )}
      <img
        src="/omnix-logo.png"
        alt="OMNIX QUANTUM"
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'contain',
          opacity,
          display: 'block',
        }}
      />
    </motion.div>
  );
}
