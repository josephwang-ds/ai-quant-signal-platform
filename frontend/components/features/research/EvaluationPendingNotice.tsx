type EvaluationPendingNoticeProps = {
  message: string;
  label?: string;
};

/**
 * Replaces a numeric confidence score when no evaluation evidence exists.
 */
export default function EvaluationPendingNotice({
  message,
  label = "Evaluation",
}: EvaluationPendingNoticeProps) {
  return (
    <div
      className="evaluation-pending-notice"
      title={`${label}: ${message}`}
      role="status"
    >
      <span className="evaluation-pending-notice__label">{label}</span>
      <p className="evaluation-pending-notice__message">{message}</p>
    </div>
  );
}
