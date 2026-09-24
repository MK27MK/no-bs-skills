import { getData } from "./api.js";

const users = await getData(1);
console.log(users.length);
