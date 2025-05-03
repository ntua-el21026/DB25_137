export const API_BASE = "http://localhost:8000/api";

export function authHeaders() {
	const token = sessionStorage.getItem("token");
	return {
		"Content-Type": "application/json",
		"Authorization": token || ""
	};
}

export async function safeFetch(url, options = {}) {
	const res = await fetch(url, options);

	if (res.status === 401 || res.status === 403) {
		sessionStorage.clear();
		window.location.href = "/login";
		throw new Error("Unauthorized");
	}

	return res;
}
