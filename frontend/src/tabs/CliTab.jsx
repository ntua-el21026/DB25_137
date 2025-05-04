import React, { useEffect, useRef, useState } from "react";
import { API_BASE, authHeaders, safeFetch } from "../api/client";

export default function CliTab() {
	const [command, setCommand] = useState("");
	const [history, setHistory] = useState(() => {
		const saved = sessionStorage.getItem("cliHistory");
		return saved ? JSON.parse(saved) : [];
	});
	const [available, setAvailable] = useState([]);
	const inputRef = useRef();

	useEffect(() => {
		safeFetch(`${API_BASE}/cli/list`, {
			method: "GET",
			headers: authHeaders()
		})
			.then(res => res.json())
			.then(data => setAvailable(data.commands || []))
			.catch(() => {});
	}, []);

	useEffect(() => {
		sessionStorage.setItem("cliHistory", JSON.stringify(history));
	}, [history]);

	const handleRun = async () => {
		let trimmed = command.trim();
		if (!trimmed) return;

		// Confirmation for destructive commands
		const dangerous = [
			"db137 drop-db",
			"db137 erase",
			"drop-db",
			"erase"
		];

		const base = trimmed.replace(/\s+--yes$/, "").trim();
		if (dangerous.includes(base)) {
			const ok = window.confirm(`Are you sure you want to run: ${base}?`);
			if (!ok) return;
			if (!trimmed.includes("--yes")) trimmed += " --yes";
		}

		setCommand("");

		try {
			const res = await fetch(`${API_BASE}/cli/run`, {
				method: "POST",
				headers: {
					...authHeaders(),
					"Content-Type": "application/json"
				},
				body: JSON.stringify({ command: trimmed })
			});
			const text = await res.text();

			setHistory(prev => [
				...prev,
				{
					command: trimmed,
					output: text.trim(),
					success: res.ok,
					expanded: true
				}
			]);
		} catch (err) {
			setHistory(prev => [
				...prev,
				{
					command: trimmed,
					output: String(err),
					success: false,
					expanded: true
				}
			]);
		}
	};

	const handleKeyDown = (e) => {
		if (e.key === "Enter") {
			e.preventDefault();
			handleRun();
		}
	};

	const handleClear = () => {
		setHistory([]);
		setCommand("");
		sessionStorage.removeItem("cliHistory");
		inputRef.current?.focus();
	};

	const toggleExpand = (index) => {
		setHistory(prev =>
			prev.map((item, i) =>
				i === index ? { ...item, expanded: !item.expanded } : item
			)
		);
	};

	return (
		<div className="p-6 bg-white rounded-xl shadow-lg">
			<h2 className="text-2xl font-bold text-blue-700 mb-4 text-center">Run CLI Commands</h2>

			<h3 className="text-base font-semibold text-gray-800 mb-2">Available Commands:</h3>
			<div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-1 mb-6 text-sm">
				{available.map(cmd => (
					<div key={cmd.name} className="flex items-start space-x-2">
						<code className="text-blue-700 font-mono">{cmd.name}</code>
						{cmd.description && (
							<span className="text-gray-500">— {cmd.description}</span>
						)}
					</div>
				))}
			</div>

			<div className="flex items-center gap-4 mb-4">
				<input
					ref={inputRef}
					type="text"
					value={command}
					onChange={(e) => setCommand(e.target.value)}
					onKeyDown={handleKeyDown}
					placeholder="Command (e.g. db137 q1, db137 users list, db137 create-db)"
					className="flex-grow px-4 py-2 border border-gray-300 rounded-lg text-sm font-mono focus:ring-2 focus:ring-blue-300"
				/>
				<button
					onClick={handleRun}
					className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition"
				>
					Run
				</button>
				<button
					onClick={handleClear}
					className="bg-gray-300 text-gray-800 px-4 py-2 rounded-lg hover:bg-gray-400 transition"
				>
					Clear
				</button>
			</div>

			<div className="space-y-4 mt-6">
				{history.map((item, idx) => (
					<div
						key={idx}
						className={`border rounded-lg ${
							item.success
								? "border-green-300 bg-green-50"
								: "border-red-300 bg-red-50"
						}`}
					>
						<button
							onClick={() => toggleExpand(idx)}
							className="w-full flex justify-between items-center px-4 py-2 font-mono font-semibold text-left text-black"
						>
							<span>$ {item.command}</span>
							<span className="text-xs text-gray-500">
								{item.expanded ? "▲ Collapse" : "▼ Expand"}
							</span>
						</button>

						{item.expanded && (
							<div className="px-4 py-3 border-t text-sm font-mono whitespace-pre-wrap break-words text-gray-800">
								{item.output}
							</div>
						)}
					</div>
				))}
			</div>
		</div>
	);
}
