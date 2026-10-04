interface SuggestedFollowUpsProps {
  suggestions: string[];
  disabled?: boolean;
  onSelect: (message: string) => void;
}

export function SuggestedFollowUps({
  suggestions,
  disabled = false,
  onSelect,
}: SuggestedFollowUpsProps) {
  if (suggestions.length === 0) {
    return null;
  }

  return (
    <div className="related-questions mt-2">
      <p className="related-questions-label">Related questions</p>
      <div className="related-questions-list">
        {suggestions.map((suggestion) => (
          <button
            key={suggestion}
            type="button"
            disabled={disabled}
            onClick={() => onSelect(suggestion)}
            className="related-questions-chip"
          >
            {suggestion}
          </button>
        ))}
      </div>
    </div>
  );
}
