type LoadingStateProps = {
  message?: string;
};

export default function LoadingState({ message = "Loading..." }: LoadingStateProps) {
  return <p className="loading-state">{message}</p>;
}
