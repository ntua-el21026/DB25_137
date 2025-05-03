import React, { useEffect, useState } from "react";
import { API_BASE, authHeaders, safeFetch } from "../api/client";

const options = ["Tables", "Views", "Triggers", "Procedures"];

export default function SchemaTab() {
	const [selected, setSelected] = useState(["Tables"]);
	const [schema, setSchema] = useState({
		Tables: [],
		Views: [],
		Triggers: [],
		Procedures: [],
	});

	useEffect(() => {
		safeFetch(`${API_BASE}/schema`, {
			method: "POST",
			headers: authHeaders(),
		})
			.then((res) => res.json())
			.then((data) => {
				setSchema({
					Tables: data.tables || [],
					Views: data.views || [],
					Triggers: data.triggers || [],
					Procedures: data.procedures || [],
				});
			});
	}, []);

	const toggle = (type) => {
		setSelected((prev) =>
			prev.includes(type)
				? prev.filter((t) => t !== type)
				: [...prev, type]
		);
	};

	return (
		<div className="p-6 bg-white rounded-xl shadow-lg">
			<h2 className="text-2xl font-bold text-blue-700 mb-6 text-center">
				Database Schema Overview
			</h2>

			<div className="flex flex-wrap justify-center gap-3 mb-8">
				{options.map((type) => (
					<button
						key={type}
						onClick={() => toggle(type)}
						className={`px-4 py-2 rounded-full font-medium transition ${
							selected.includes(type)
								? "bg-blue-600 text-white"
								: "bg-gray-200 text-gray-700 hover:bg-gray-300"
						}`}
					>
						{type}
					</button>
				))}
			</div>

			<div className="grid sm:grid-cols-2 gap-6">
				{selected.map((type) => (
					<div
						key={type}
						className="bg-gray-50 p-4 rounded-lg shadow-inner border border-gray-100"
					>
						<h3 className="text-lg font-semibold text-blue-600 mb-2">
							{type}
						</h3>
						<ul className="text-sm text-gray-700 list-disc list-inside space-y-1">
							{schema[type].map((item) => (
								<li key={item}>{item}</li>
							))}
							{schema[type].length === 0 && (
								<li className="italic text-gray-500">None found.</li>
							)}
						</ul>
					</div>
				))}
			</div>
		</div>
	);
}
