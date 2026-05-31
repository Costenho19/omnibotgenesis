import { motion } from 'framer-motion';
import type { CSSProperties } from 'react';

interface OmnixLogoProps {
  size?: string | number;
  opacity?: number;
  animate?: boolean;
  glow?: boolean;
  className?: string;
  style?: CSSProperties;
}

export function OmnixLogo({
  size = '8vw',
  opacity = 1,
  glow = false,
  className,
  style,
}: OmnixLogoProps) {
  return (
    <motion.div
      className={className}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: `calc(${typeof size === 'number' ? size + 'px' : size} * 0.2)`,
        position: 'relative',
        flexShrink: 0,
        opacity,
        ...style,
      }}
    >
      {glow && (
        <div
          style={{
            position: 'absolute',
            inset: '-30%',
            borderRadius: '50%',
            background: 'radial-gradient(circle, rgba(212,168,67,0.18) 0%, transparent 70%)',
            pointerEvents: 'none',
            zIndex: 0
          }}
        />
      )}
      <div 
        style={{ width: size, height: size, backgroundColor: '#050508', border: '1px solid rgba(212,168,67,0.5)', zIndex: 1 }}
        className="flex items-center justify-center relative overflow-hidden shrink-0"
      >
        <div className="w-[45%] h-[45%] bg-[#D4A843]" style={{ clipPath: 'polygon(0 0, 100% 0, 100% 100%, 50% 50%, 0 100%)' }} />
        <div className="absolute w-[60%] h-[2px] bg-[#D4A843] bottom-[20%]" />
      </div>
      <div className="flex flex-col justify-center relative z-10">
        <span className="text-white font-display font-bold tracking-[0.2em] leading-none" style={{ fontSize: `calc(${typeof size === 'number' ? size + 'px' : size} * 0.4)` }}>OMNIX</span>
        <span className="text-[#D4A843] font-mono tracking-[0.3em] leading-none mt-2" style={{ fontSize: `calc(${typeof size === 'number' ? size + 'px' : size} * 0.15)` }}>QUANTUM</span>
      </div>
    </motion.div>
  );
}
