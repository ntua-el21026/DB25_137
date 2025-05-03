import { useEffect, useState } from "react";
import { API_BASE, authHeaders, safeFetch } from "../api/client";

export function useSchema() {
	const [schema, setSchema] = useState({
		Tables: [],
		Views: [],
		Triggers: [],
		Procedures: []
	});

	const fetchSchema = async () => {
		const res = await safeFetch(`${API_BASE}/schema`, {
			method: "POST",
			headers: authHeaders()
		});
		const data = await res.json();
		setSchema({
			Tables: data.tables || [],
			Views: data.views || [],
			Triggers: data.triggers || [],
			Procedures: data.procedures || []
		});
	};

	useEffect(() => {
		fetchSchema();
	}, []);

	return [schema, fetchSchema];
}
