type ErrorAlertProps = {
  title?: string;
  message: string;
};

export default function ErrorAlert({ title, message }: ErrorAlertProps) {
  return (
    <div className="error-alert" role="alert">
      {title ? <p className="error-alert__title">{title}</p> : null}
      <p>{message}</p>
    </div>
  );
}
