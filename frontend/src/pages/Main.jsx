import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import SchemaTab from "../tabs/SchemaTab";
import BrowseTab from "../tabs/BrowseTab";
import QueryTab from "../tabs/QueryTab";
import CliTab from "../tabs/CliTab";
import SessionTimer from "../components/SessionTimer";

const tabs = ["Schema Overview", "Browse Schema", "Run Query", "Run Cli"];

export default function Main() {
	const [activeTab, setActiveTab] = useState("Schema Overview");
	const [cliHistory, setCliHistory] = useState([]);
	const navigate = useNavigate();

	return (
		<div className="min-h-screen bg-gradient-to-br from-blue-50 to-blue-100 text-gray-800">
			<header className="sticky top-0 bg-white shadow z-10 relative">
				<button
					onClick={() => navigate("/logout")}
					className="absolute top-4 right-6 flex items-center gap-2 bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition"
					aria-label="Logout"
				>
					<svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
						<path strokeLinecap="round" strokeLinejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H9m6-7V5a2 2 0 00-2-2H5a2 2 0 00-2 2v14a2 2 0 002 2h8a2 2 0 002-2v-1"/>
					</svg>
					<span>Logout</span>
				</button>

				<div className="text-center py-6">
					<h1 className="text-3xl font-extrabold text-blue-700">
						Pulse University Frontend
					</h1>
					<h2 className="text-xl font-semibold text-blue-600 mt-1">
						DB137 Database
					</h2>
				</div>

				<nav className="border-t border-gray-200 bg-white">
					<div className="flex justify-center space-x-6 max-w-6xl mx-auto px-6">
						{tabs.map((tab) => (
							<button
								key={tab}
								onClick={() => setActiveTab(tab)}
								className={`py-3 px-4 text-sm font-medium rounded-full transition ${
									activeTab === tab
										? "bg-blue-600 text-white"
										: "text-gray-500 hover:bg-blue-50 hover:text-blue-600"
								}`}
							>
								{tab}
							</button>
						))}
					</div>
				</nav>
			</header>

			<SessionTimer />

			<main className="max-w-6xl mx-auto px-6 py-8">
				{activeTab === "Schema Overview" && <SchemaTab />}
				{activeTab === "Browse Schema" && <BrowseTab />}
				{activeTab === "Run Query" && <QueryTab />}
				{activeTab === "Run Cli" && (
					<CliTab history={cliHistory} setHistory={setCliHistory} />
				)}
			</main>
		</div>
	);
}
