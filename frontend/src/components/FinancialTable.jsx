export default function FinancialTable({ data }) {
  return (
    <table className="fin-table">
      <thead>
        <tr>
          <th>Indicator</th>
          <th>Value</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        {data.map((r, i) => (
          <tr key={i} className={r.status}>
            <td>{r.name}</td>
            <td>{r.value ?? "-"}</td>
            <td>{r.status}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
