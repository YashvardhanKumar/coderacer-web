export function Loader() {
    return (
        <div className="flex items-center justify-center min-h-screen">
            <div className="relative">
                {/* Outer rotating ring */}
                <div className="absolute inset-0 flex items-center justify-center">
                    <div className="w-32 h-32 rounded-full border-4 border-transparent border-t-cyan-400 border-r-purple-500 animate-spin"
                        style={{ animationDuration: '1s' }}></div>
                </div>

                {/* Inner pulsing ring */}
                <div className="absolute inset-0 flex items-center justify-center">
                    <div className="w-24 h-24 rounded-full border-2 border-purple-400 opacity-50 animate-ping"></div>
                </div>

                {/* Center content */}
                <div className="relative flex flex-col items-center justify-center w-32 h-32">
                    {/* Code brackets with animation */}
                    <div className="flex items-center justify-center gap-1 mb-2">
                        <span className="text-2xl font-bold text-cyan-400 animate-pulse"
                            style={{ animationDuration: '1.5s' }}>{'<'}</span>
                        <span className="text-2xl font-bold text-purple-400 animate-pulse"
                            style={{ animationDuration: '1.5s', animationDelay: '0.2s' }}>{'/'}</span>
                        <span className="text-2xl font-bold text-cyan-400 animate-pulse"
                            style={{ animationDuration: '1.5s', animationDelay: '0.4s' }}>{'>'}</span>
                    </div>

                    {/* Racing flag checkered pattern */}
                    <div className="flex gap-0.5 mb-2">
                        <div className="w-1.5 h-1.5 bg-white animate-pulse" style={{ animationDelay: '0s' }}></div>
                        <div className="w-1.5 h-1.5 bg-slate-800 animate-pulse" style={{ animationDelay: '0.1s' }}></div>
                        <div className="w-1.5 h-1.5 bg-white animate-pulse" style={{ animationDelay: '0.2s' }}></div>
                        <div className="w-1.5 h-1.5 bg-slate-800 animate-pulse" style={{ animationDelay: '0.3s' }}></div>
                    </div>
                    <div className="flex gap-0.5">
                        <div className="w-1.5 h-1.5 bg-slate-800 animate-pulse" style={{ animationDelay: '0.4s' }}></div>
                        <div className="w-1.5 h-1.5 bg-white animate-pulse" style={{ animationDelay: '0.5s' }}></div>
                        <div className="w-1.5 h-1.5 bg-slate-800 animate-pulse" style={{ animationDelay: '0.6s' }}></div>
                        <div className="w-1.5 h-1.5 bg-white animate-pulse" style={{ animationDelay: '0.7s' }}></div>
                    </div>
                </div>

                {/* Speed lines */}
                <div className="absolute top-1/2 -left-20 w-16 h-0.5 bg-gradient-to-r from-transparent to-cyan-400 animate-pulse"
                    style={{ animationDuration: '0.8s' }}></div>
                <div className="absolute top-1/2 -left-16 w-12 h-0.5 bg-gradient-to-r from-transparent to-purple-400 animate-pulse mt-2"
                    style={{ animationDuration: '0.8s', animationDelay: '0.2s' }}></div>
                <div className="absolute top-1/2 -left-20 w-16 h-0.5 bg-gradient-to-r from-transparent to-cyan-400 animate-pulse -mt-2"
                    style={{ animationDuration: '0.8s', animationDelay: '0.4s' }}></div>
            </div>

            {/* Company name */}
            <div className="absolute bottom-1/3">
                <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-purple-500 animate-pulse"
                    style={{ animationDuration: '2s' }}>
                    Coderacer
                </h1>
                <div className="flex justify-center gap-1 mt-2">
                    <div className="w-2 h-2 rounded-full bg-cyan-400 animate-bounce" style={{ animationDelay: '0s' }}></div>
                    <div className="w-2 h-2 rounded-full bg-purple-400 animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                    <div className="w-2 h-2 rounded-full bg-cyan-400 animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                </div>
            </div>
        </div>
    );
}

export function LoaderSmall({ size = 'md' }) {
  const sizes: Record<string, string> = {
    sm: 'w-8 h-8',
    md: 'w-12 h-12',
    lg: 'w-16 h-16'
  };

  const iconSizes: Record<string, string> = {
    sm: 'text-xs',
    md: 'text-sm',
    lg: 'text-base'
  };

  const ringWidths: Record<string, string> = {
    sm: 'border-2',
    md: 'border-2',
    lg: 'border-3'
  };

  return (
    <div className="inline-flex items-center justify-center">
      <div className="relative">
        {/* Outer rotating ring */}
        <div className={`${sizes[size]} rounded-full ${ringWidths[size]} border-transparent border-t-cyan-400 border-r-purple-500 animate-spin`}
             style={{ animationDuration: '0.8s' }}></div>
        
        {/* Center icon */}
        <div className="absolute inset-0 flex items-center justify-center">
          <div className={`${iconSizes[size]} font-bold text-cyan-400`}>
            {'</>'}
          </div>
        </div>
      </div>
    </div>
  );
}