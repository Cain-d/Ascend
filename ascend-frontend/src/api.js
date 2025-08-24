// src/api.js
import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:8000",
});

api.interceptors.request.use((config) => {
  const token = sessionStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export async function fetchDailyMacros() {
  try {
    const response = await api.get("/daily_macros");
    return response.data;
  } catch (err) {
    throw new Error("Failed to fetch daily macros");
  }
}

// Analytics API functions
export async function fetchAnalyticsTrends(days = 30) {
  try {
    const response = await api.get(`/analytics/trends?days=${days}`);
    return response.data;
  } catch (err) {
    throw err;
  }
}

export async function fetchAnalyticsPredictions(workoutType = "general") {
  try {
    const response = await api.get(`/analytics/predictions?workout_type=${workoutType}`);
    return response.data;
  } catch (err) {
    throw err;
  }
}

export async function fetchAnalyticsRecommendations(goalType = "maintenance") {
  try {
    const response = await api.get(`/analytics/recommendations?goal_type=${goalType}`);
    return response.data;
  } catch (err) {
    throw err;
  }
}

export async function fetchAnalyticsInsights() {
  try {
    const response = await api.get("/analytics/insights");
    return response.data;
  } catch (err) {
    throw err;
  }
}

export default api;

