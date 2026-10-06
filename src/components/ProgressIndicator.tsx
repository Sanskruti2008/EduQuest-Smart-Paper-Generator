const ProgressIndicator = ({ currentStep }) => {
  const steps = [
    { number: 1, label: 'Mode' },
    { number: 2, label: 'Configure' },
    { number: 3, label: 'Build' },
    { number: 4, label: 'Review' },
    { number: 5, label: 'Export' }
  ];

  return (
    <div className="flex justify-center items-center gap-3 mb-10">
      {steps.map((step, index) => (
        <div key={step.number} className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <div className={`
              w-9 h-9 rounded-full flex items-center justify-center text-sm font-semibold transition-all
              ${currentStep === step.number ? 'bg-gray-900 text-white shadow-lg' : 
                currentStep > step.number ? 'bg-gray-700 text-white' : 
                'bg-gray-100 text-gray-400'}
            `}>
              {currentStep > step.number ? '✓' : step.number}
            </div>
            <span className={`hidden sm:inline text-sm font-medium ${
              currentStep >= step.number ? 'text-gray-900' : 'text-gray-400'
            }`}>
              {step.label}
            </span>
          </div>
          {index < steps.length - 1 && (
            <div className={`w-10 h-0.5 hidden md:block transition-all ${
              currentStep > step.number ? 'bg-gray-700' : 'bg-gray-200'
            }`} />
          )}
        </div>
      ))}
    </div>
  );
};

export default ProgressIndicator;
