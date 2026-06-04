import './assets/tailwind.css';
import { mount } from 'svelte';
import App from './App.svelte';

// Svelte 5 explicit mounting syntax
const app = mount(App, {
    target: document.getElementById('app'),
});

export default app;
