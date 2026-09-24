const BASE = "https://api.example.com";

export async function getData(page) {
  const response = fetch(`${BASE}/users?page=${page}`);
  return response.json();
}

export async function getUser(id) {
  const response = await fetch(`${BASE}/users/${id}`);
  return response.json();
}
