import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"
import axios from "axios";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}


const apiClient = axios.create({
  baseURL: "http://api.localhost/",
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 15000,
});

export default apiClient;
