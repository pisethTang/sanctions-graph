import { createRouter, createWebHistory } from "vue-router";
import AgentForm from "../views/AgentForm.vue";
import CaseList from "../views/CaseList.vue";
import CaseDetail from "../views/CaseDetail.vue";

const routes = [
  { path: "/", name: "new-screening", component: AgentForm },
  { path: "/cases", name: "cases", component: CaseList },
  { path: "/cases/:id", name: "case-detail", component: CaseDetail },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
