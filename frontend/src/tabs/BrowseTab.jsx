import React, { useEffect, useState } from "react";
import CodeMirror from "@uiw/react-codemirror";
import { sql } from "@codemirror/lang-sql";
import { API_BASE, authHeaders, safeFetch } from "../api/client";

const CATEGORIES = ["Tables", "Views", "Triggers", "Procedures"];

function download(content, filename, type = "text/plain") {
	const blob = new Blob([content], { type });
	const url = URL.createObjectURL(blob);
	const a = document.createElement("a");
	a.href = url;
	a.download = filename;
	a.click();
	URL.revokeObjectURL(url);
}

export default function BrowseTab() {
	const [schema, setSchema] = useState({
		Tables: [],
		Views: [],
		Procedures: [],
		Triggers: []
	});
	const [category, setCategory] = useState("Tables");
	const [selectedItem, setSelectedItem] = useState("");
	const [definition, setDefinition] = useState("");
	const [rows, setRows] = useState([]);
	const [copied, setCopied] = useState(false);

	useEffect(() => {
		safeFetch(`${API_BASE}/schema`, {
			method: "POST",
			headers: authHeaders()
		})
			.then((res) => res.json())
			.then((data) => {
				setSchema({
					Tables: data.tables || [],
					Views: data.views || [],
					Procedures: data.procedures || [],
					Triggers: data.triggers || []
				});
				const initial = (data.tables || [])[0] || "";
				setSelectedItem(initial);
			});
	}, []);

	useEffect(() => {
		if (!selectedItem) return;

		let endpoint = "";
		if (category === "Tables") {
			endpoint = `/definition/${selectedItem}`;
		} else if (category === "Views") {
			endpoint = `/view_definition/${selectedItem}`;
		} else if (category === "Procedures") {
			endpoint = `/procedure_definition/${selectedItem}`;
		} else if (category === "Triggers") {
			endpoint = `/trigger_definition/${selectedItem}`;
		}

		safeFetch(`${API_BASE}${endpoint}`)
			.then((res) => res.text())
			.then(setDefinition);

		if (category === "Tables") {
			safeFetch(`${API_BASE}/browse/${selectedItem}`, {
				method: "POST",
				headers: authHeaders()
			})
				.then((res) => res.json())
				.then(setRows);
		} else {
			setRows([]);
		}
	}, [selectedItem, category]);

	const copyDefinition = () => {
		navigator.clipboard.writeText(definition);
		setCopied(true);
		setTimeout(() => setCopied(false), 2000);
	};

	const exportCSV = () => {
		if (!rows.length) return;
		const header = Object.keys(rows[0]).join(",");
		const body = rows.map(row => Object.values(row).join(",")).join("\n");
		download(`${header}\n${body}`, `${selectedItem}.csv`, "text/csv");
	};

	const exportTXT = () => {
		if (!rows.length) return;
		const lines = rows.map(row =>
			Object.entries(row)
				.map(([key, val]) => `${key}: ${val}`)
				.join(" | ")
		);
		download(lines.join("\n"), `${selectedItem}.txt`);
	};

	return (
		<div className="p-6 bg-white rounded-xl shadow-lg">
			<h2 className="text-2xl font-bold text-blue-700 mb-6 text-center">
				Database Schema Overview
			</h2>

			<div className="flex justify-center gap-3 mb-4 flex-wrap">
				{CATEGORIES.map((type) => (
					<button
						key={type}
						onClick={() => {
							setCategory(type);
							const first = schema[type][0] || "";
							setSelectedItem(first);
						}}
						className={`px-4 py-2 rounded-full text-sm font-medium transition ${
							category === type
								? "bg-blue-600 text-white"
								: "bg-gray-200 text-gray-700 hover:bg-gray-300"
						}`}
					>
						{type}
					</button>
				))}
			</div>

			<div className="flex justify-center gap-3 mb-6 flex-wrap">
				{schema[category].map((item) => (
					<button
						key={item}
						onClick={() => setSelectedItem(item)}
						className={`px-4 py-2 rounded-lg text-xs font-medium transition ${
							item === selectedItem
								? "bg-blue-500 text-white"
								: "bg-gray-100 text-gray-800 hover:bg-gray-200"
						}`}
					>
						{item}
					</button>
				))}
			</div>

			{category === "Tables" ? (
				<div className="grid lg:grid-cols-2 gap-6">
					<div>
						<div className="flex items-center justify-between mb-2">
							<h3 className="text-lg font-semibold text-blue-600">
								Table Definition
							</h3>
							<div className="flex items-center gap-2">
								<button
									onClick={copyDefinition}
									className="bg-blue-100 text-blue-700 text-sm font-medium px-3 py-1 rounded hover:bg-blue-200 transition"
								>
									Copy to Clipboard
								</button>
								{copied && (
									<span className="text-green-600 text-sm font-medium animate-pulse">
										Copied!
									</span>
								)}
							</div>
						</div>
						<CodeMirror
							value={definition}
							extensions={[sql()]}
							editable={false}
							className="w-full p-0 border border-gray-300 rounded-lg font-mono text-sm min-h-[12rem] max-h-[50vh] overflow-auto"
						/>
					</div>

					<div className="overflow-x-auto">
						<div className="flex items-center justify-between mb-2">
							<h3 className="text-lg font-semibold text-blue-600">
								Table Data
							</h3>
							<div className="flex gap-2">
								<button
									onClick={exportCSV}
									className="text-sm text-blue-600 hover:underline"
								>
									Export CSV
								</button>
								<button
									onClick={exportTXT}
									className="text-sm text-blue-600 hover:underline"
								>
									Export TXT
								</button>
							</div>
						</div>
						{rows.length > 0 ? (
							<table className="min-w-full text-sm border border-gray-200 rounded-lg overflow-hidden">
								<thead className="bg-blue-50">
									<tr>
										{Object.keys(rows[0]).map((col) => (
											<th key={col} className="px-4 py-2 text-left font-medium text-gray-700 border-b">
												{col}
											</th>
										))}
									</tr>
								</thead>
								<tbody className="divide-y divide-gray-100">
									{rows.map((row, idx) => (
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
						) : (
							<p className="text-center text-gray-500">No data available.</p>
						)}
					</div>
				</div>
			) : (
				<div className="max-w-4xl mx-auto">
					<div className="flex items-center justify-between mb-2">
						<h3 className="text-lg font-semibold text-blue-600">
							{category.slice(0, -1)} Definition
						</h3>
						<div className="flex items-center gap-2">
							<button
								onClick={copyDefinition}
								className="bg-blue-100 text-blue-700 text-sm font-medium px-3 py-1 rounded hover:bg-blue-200 transition"
							>
								Copy to Clipboard
							</button>
							{copied && (
								<span className="text-green-600 text-sm font-medium animate-pulse">
									Copied!
								</span>
							)}
						</div>
					</div>
					<CodeMirror
						value={definition}
						extensions={[sql()]}
						editable={false}
						className="w-full p-0 border border-gray-300 rounded-lg font-mono text-sm min-h-[12rem] max-h-[60vh] overflow-auto"
					/>
				</div>
			)}
		</div>
	);
}
