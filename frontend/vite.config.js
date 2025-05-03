import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
	server: {
		port: 4000,
		historyApiFallback: true
	},
	optimizeDeps: {
		include: [
			'@uiw/react-codemirror',
			'@codemirror/lang-sql'
		]
	},
	plugins: [react()]
});
