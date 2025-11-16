interface Props {
  selectedAccount: string;
  onAccountChange: (account: string) => void;
}

export default function AccountFilter({ selectedAccount, onAccountChange }: Props) {
  const accounts = ['All', 'Trading', 'ISA'];

  return (
    <div className="flex gap-2 mb-6">
      {accounts.map((account) => (
        <button
          key={account}
          onClick={() => onAccountChange(account)}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
            selectedAccount === account
              ? 'bg-blue-600 text-white'
              : 'bg-portfolio-card text-portfolio-text-dim hover:bg-portfolio-border hover:text-portfolio-text'
          }`}
        >
          {account}
        </button>
      ))}
    </div>
  );
}
