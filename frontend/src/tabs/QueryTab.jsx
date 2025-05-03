import React, { useState } from "react";
import CodeMirror from "@uiw/react-codemirror";
import { sql } from "@codemirror/lang-sql";
import { API_BASE, authHeaders, safeFetch } from "../api/client";
import { useSchema } from "../hooks/useSchema";

export default function QueryTab() {
	const [query, setQuery] = useState("");
	const [result, setResult] = useState(null);
	const [error, setError] = useState("");
	const [success, setSuccess] = useState(false);
	const [, refreshSchema] = useSchema();

	const handleSubmit = async (e) => {
		e.preventDefault();
		setError("");
		setResult(null);
		setSuccess(false);

		try {
			const res = await safeFetch(`${API_BASE}/query`, {
				method: "POST",
				headers: authHeaders(),
				body: JSON.stringify({ sql: query.trim() }),
			});
			const data = await res.json();

			if (res.status === 403 || (data.error && /access denied/i.test(data.error))) {
				setQuery("");
				setError("You do not have permission to execute this query.");
				return;
			}

			if (data.status === "OK") {
				setSuccess(true);
				setQuery("");
			} else if (Array.isArray(data)) {
				setResult(data);
			} else {
				setError(data.error || "Unknown error");
			}

			await refreshSchema();
		} catch (err) {
			setError(err.message);
		}
	};

	return (
		<div className="p-6 bg-white rounded-xl shadow-lg">
			<h2 className="text-2xl font-bold text-blue-700 mb-6 text-center">Run SQL Query</h2>

			<form onSubmit={handleSubmit} className="space-y-4">
				<CodeMirror
					autoFocus
					value={query}
					onChange={setQuery}
					extensions={[sql()]}
					className="w-full min-h-[12rem] max-h-[50vh] overflow-auto border border-gray-300 rounded-lg font-mono text-sm focus:ring-2 focus:ring-blue-300 transition"
				/>
				<div className="flex justify-end">
					<button
						type="submit"
						className="bg-gradient-to-r from-blue-500 to-blue-600 text-white px-6 py-2 rounded-lg hover:from-blue-600 hover:to-blue-700 transition"
					>
						Execute
					</button>
				</div>
			</form>

			{error && <p className="text-red-600 mt-4 text-center">{error}</p>}
			{success && <p className="text-green-600 mt-4 text-center">Query executed successfully.</p>}

			{result && result.length > 0 && (
				<div className="overflow-x-auto mt-8">
					<table className="min-w-full text-sm border border-gray-200 rounded-lg overflow-hidden">
						<thead className="bg-blue-50">
							<tr>
								{Object.keys(result[0]).map((col) => (
									<th key={col} className="px-4 py-2 text-left font-medium text-gray-700 border-b">
										{col}
									</th>
								))}
							</tr>
						</thead>
						<tbody className="divide-y divide-gray-100">
							{result.map((row, idx) => (
								<tr key={idx} className="hover:bg-gray-50">
									{Object.values(row).map((val, i) => (
										<td key={i} className="px-4 py-2 border-b text-gray-800">
											{val}
										</td>
									))}
								</tr>
							))}
						</tbody>
					</table>
				</div>
			)}
		</div>
	);
}
