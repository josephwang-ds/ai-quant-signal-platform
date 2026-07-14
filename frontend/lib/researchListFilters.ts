/**
 * Research List 筛选与排序。
 *
 * TODO(backend): 服务端分页/筛选就绪后，将本地过滤改为查询参数映射。
 */

import type { ResearchLifecycleStatus, ResearchListItem } from "@/types/research";

export type ResearchListSort = "updated" | "created" | "name" | "confidence";

export type ResearchListFilters = {
  query: string;
  status: ResearchLifecycleStatus | "all";
  owner: string | "all";
  tag: string | "all";
  sort: ResearchListSort;
};

export const DEFAULT_RESEARCH_LIST_FILTERS: ResearchListFilters = {
  query: "",
  status: "all",
  owner: "all",
  tag: "all",
  sort: "updated",
};

export function getUniqueResearchOwners(items: ResearchListItem[]): string[] {
  return Array.from(new Set(items.map((item) => item.owner))).sort();
}

export function getUniqueResearchTags(items: ResearchListItem[]): string[] {
  return Array.from(new Set(items.flatMap((item) => item.tags))).sort();
}

export function filterAndSortResearchList(
  items: ResearchListItem[],
  filters: ResearchListFilters
): ResearchListItem[] {
  const query = filters.query.trim().toLowerCase();

  const filtered = items.filter((item) => {
    if (filters.status !== "all" && item.status !== filters.status) {
      return false;
    }
    if (filters.owner !== "all" && item.owner !== filters.owner) {
      return false;
    }
    if (filters.tag !== "all" && !item.tags.includes(filters.tag)) {
      return false;
    }
    if (!query) {
      return true;
    }
    const haystack = [
      item.name,
      item.researchQuestion,
      item.owner,
      item.currentRecommendation,
      ...item.tags,
    ]
      .join(" ")
      .toLowerCase();
    return haystack.includes(query);
  });

  const sorted = [...filtered];
  sorted.sort((a, b) => {
    switch (filters.sort) {
      case "name":
        return a.name.localeCompare(b.name);
      case "confidence":
        return (b.confidenceScore ?? -1) - (a.confidenceScore ?? -1);
      case "created":
        return Date.parse(b.createdAt) - Date.parse(a.createdAt);
      case "updated":
      default:
        return Date.parse(b.updatedAt) - Date.parse(a.updatedAt);
    }
  });

  return sorted;
}
