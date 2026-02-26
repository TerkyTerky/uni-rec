import axios from "axios"

const client = axios.create({
  baseURL: "http://localhost:8000/api",
  timeout: 10000
})

export type RecommendPayload = {
  reviewerID: string
  top_k: number
  threshold: number
  mode: string
  use_llm: boolean
}

export type FeedbackPayload = {
  reviewerID: string
  asin: string
  action: "like" | "dislike" | "save"
}

export type GeneratePayload = {
  users: number
  items: number
  behaviors_per_user: number
  social_degree: number
  seed: number
}

export const fetchUserProfile = (reviewerID: string) => client.get(`/users/${reviewerID}`)
export const fetchStartupType = (reviewerID: string, threshold: number) =>
  client.get(`/users/${reviewerID}/startup-type`, { params: { threshold } })
export const fetchSequence = (reviewerID: string) => client.get(`/users/${reviewerID}/sequence`)
export const fetchSocialGraph = (reviewerID: string) => client.get(`/users/${reviewerID}/social-graph`)
export const requestRecommend = (payload: RecommendPayload) => client.post("/recommend", payload)
export const sendFeedback = (payload: FeedbackPayload) => client.post("/feedback", payload)
export const fetchMetrics = () => client.get("/metrics")
export const generateData = (payload: GeneratePayload) => client.post("/data/generate", payload)
export const fetchUsers = () => client.get("/users")
